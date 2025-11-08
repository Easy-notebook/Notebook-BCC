"""
Response Parser for Planning/Reflecting/Generating API responses.
Handles XML and JSON response formats from different API endpoints.
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from silantui import ModernLogger


class ResponseParser(ModernLogger):
    """
    Parser for API responses.

    Handles different response formats:
    - XML for workflow definitions (stages, steps, behaviors)
    - JSON for standard API responses
    """

    def __init__(self):
        """Initialize the response parser."""
        super().__init__("ResponseParser")

    def parse_response(self, response: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse API response and determine its type.

        Args:
            response: Raw response (string or dict)

        Returns:
            Parsed response with type indicator
        """
        # If already a dict, check if it has standard JSON response fields
        if isinstance(response, dict):
            return {
                'type': 'json',
                'content': response
            }

        # If string, try to parse as XML or JSON
        if isinstance(response, str):
            response = response.strip()

            # Check if it's XML
            if response.startswith('<'):
                return self._parse_xml_response(response)

            # Try to parse as JSON
            try:
                json_content = json.loads(response)
                return {
                    'type': 'json',
                    'content': json_content
                }
            except json.JSONDecodeError:
                self.error(f"Failed to parse response: {response[:100]}")
                return {
                    'type': 'unknown',
                    'content': response
                }

        self.error(f"Unsupported response type: {type(response)}")
        return {
            'type': 'unknown',
            'content': response
        }

    def _parse_xml_response(self, xml_string: str) -> Dict[str, Any]:
        """
        Parse XML response and determine its content type.

        Args:
            xml_string: XML string

        Returns:
            Dict with type and parsed content
        """
        try:
            # Pre-process: escape special characters in text content (not in tags)
            # This handles cases where API returns unescaped < > & in text
            xml_string = self._preprocess_xml(xml_string)

            root = ET.fromstring(xml_string)

            # Check root tag to determine content type
            if root.tag == 'stages':
                return {
                    'type': 'stages',
                    'content': self._parse_stages_xml(root)
                }
            elif root.tag == 'steps':
                return {
                    'type': 'steps',
                    'content': self._parse_steps_xml(root)
                }
            elif root.tag == 'behavior':
                return {
                    'type': 'behavior',
                    'content': self._parse_behavior_xml(root)
                }
            else:
                self.warning(f"Unknown XML root tag: {root.tag}")
                return {
                    'type': 'xml',
                    'content': xml_string
                }
        except ET.ParseError as e:
            self.error(f"XML parse error: {e}")
            return {
                'type': 'unknown',
                'content': xml_string
            }

    def _parse_stages_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parse <stages> XML definition.

        Returns:
            Dict with stages list and focus
        """
        stages = []
        focus = ""

        for child in root:
            if child.tag == 'stage':
                stage = self._parse_stage_element(child)
                stages.append(stage)
            elif child.tag == 'focus':
                # Clean up whitespace
                focus = (child.text or "").strip()

        return {
            'stages': stages,
            'focus': focus
        }

    def _parse_stage_element(self, element: ET.Element) -> Dict[str, Any]:
        """Parse a single <stage> element."""
        stage = {
            'stage_id': element.get('id'),
            'title': element.get('title', ''),
            'goal': '',
            'verified_artifacts': {},
            'required_variables': {}
        }

        for child in element:
            if child.tag == 'goal':
                # Clean up whitespace
                stage['goal'] = (child.text or "").strip()
            elif child.tag == 'verified_artifacts':
                stage['verified_artifacts'] = self._parse_variables_dict(child)
            elif child.tag == 'required_variables':
                stage['required_variables'] = self._parse_variables_dict(child)

        return stage

    def _parse_steps_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parse <steps> XML definition.

        Returns:
            Dict with steps list, focus, and goals
        """
        steps = []
        focus = ""
        goals = ""

        for child in root:
            if child.tag == 'step':
                step = self._parse_step_element(child)
                steps.append(step)
            elif child.tag == 'focus':
                focus = child.text or ""
            elif child.tag == 'goals':
                goals = child.text or ""

        return {
            'steps': steps,
            'focus': focus,
            'goals': goals
        }

    def _parse_step_element(self, element: ET.Element) -> Dict[str, Any]:
        """Parse a single <step> element."""
        step = {
            'step_id': element.get('id'),
            'title': element.get('title', ''),
            'goal': '',
            'verified_artifacts': {},
            'required_variables': {},
            'pcs_considerations': {}
        }

        for child in element:
            if child.tag == 'goal':
                # Clean up whitespace
                step['goal'] = (child.text or "").strip()
            elif child.tag == 'verified_artifacts':
                step['verified_artifacts'] = self._parse_variables_dict(child)
            elif child.tag == 'required_variables':
                step['required_variables'] = self._parse_variables_dict(child)
            elif child.tag == 'pcs_considerations':
                step['pcs_considerations'] = self._parse_pcs_considerations(child)

        return step

    def _parse_behavior_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parse <behavior> XML definition.

        Returns:
            Dict with behavior details
        """
        behavior = {
            'behavior_id': root.get('id'),
            'step_id': root.get('step_id'),
            'agent': '',
            'task': '',
            'inputs': {},
            'effects': None,
            'outputs': {},
            'acceptance': [],
            'whathappened': {}
        }

        for child in root:
            if child.tag == 'agent':
                behavior['agent'] = child.text or ""
            elif child.tag == 'task':
                behavior['task'] = child.text or ""
            elif child.tag == 'inputs':
                behavior['inputs'] = self._parse_variables_dict(child)
            elif child.tag == 'effects':
                # Parse effects value (could be "False" or a dict)
                effects_text = child.text or "False"
                if effects_text.strip().lower() == 'false':
                    behavior['effects'] = False
                else:
                    behavior['effects'] = effects_text
            elif child.tag == 'outputs':
                behavior['outputs'] = self._parse_outputs(child)
            elif child.tag == 'acceptance':
                behavior['acceptance'] = self._parse_acceptance(child)
            elif child.tag == 'whathappened':
                behavior['whathappened'] = self._parse_whathappened(child)

        return behavior

    def _parse_variables_dict(self, element: ET.Element) -> Dict[str, str]:
        """Parse a dictionary of variables."""
        variables = {}
        for var in element.findall('variable'):
            name = var.get('name')
            value = (var.text or "").strip()  # Clean up whitespace
            if name:
                variables[name] = value
        return variables

    def _parse_outputs(self, element: ET.Element) -> Dict[str, str]:
        """Parse outputs (artifacts)."""
        outputs = {}
        for artifact in element.findall('artifact'):
            name = artifact.get('name')
            description = artifact.text or ""
            if name:
                outputs[name] = description
        return outputs

    def _parse_acceptance(self, element: ET.Element) -> List[str]:
        """Parse acceptance criteria."""
        criteria = []
        for criterion in element.findall('criterion'):
            if criterion.text:
                criteria.append(criterion.text)
        return criteria

    def _parse_whathappened(self, element: ET.Element) -> Dict[str, str]:
        """Parse whathappened section."""
        whathappened = {}
        for child in element:
            if child.text:
                whathappened[child.tag] = child.text
        return whathappened

    def _parse_pcs_considerations(self, element: ET.Element) -> Dict[str, str]:
        """Parse PCS considerations."""
        pcs = {}
        for child in element:
            if child.text:
                pcs[child.tag] = child.text
        return pcs

    def _preprocess_xml(self, xml_string: str) -> str:
        """
        Preprocess XML to handle special characters in text content.
        Uses a state machine to properly escape content while preserving tags.
        """
        result = []
        i = 0
        in_tag = False

        while i < len(xml_string):
            char = xml_string[i]

            if not in_tag and char == '<':
                # Check if this is a real tag start (followed by letter, / or ?)
                if i + 1 < len(xml_string) and xml_string[i+1] in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/?!':
                    # Real tag
                    in_tag = True
                    result.append(char)
                else:
                    # Not a real tag, escape it
                    result.append('&lt;')
            elif in_tag and char == '>':
                # Exiting a tag
                in_tag = False
                result.append(char)
            elif not in_tag:
                # We're in text content, escape special chars
                if char == '&':
                    # Check if already escaped
                    if i + 3 < len(xml_string) and xml_string[i:i+4] in ['&lt;', '&gt;']:
                        result.append(char)
                    elif i + 4 < len(xml_string) and xml_string[i:i+5] == '&amp;':
                        result.append(char)
                    else:
                        result.append('&amp;')
                elif char == '>':
                    result.append('&gt;')
                else:
                    result.append(char)
            else:
                # In tag, keep as is
                result.append(char)

            i += 1

        return ''.join(result)


# Create singleton instance
response_parser = ResponseParser()
