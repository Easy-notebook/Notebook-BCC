"""
Response Parser for Planning/Reflecting/Generating API responses.
Handles XML and JSON response formats from different API endpoints.
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
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
        self.xml_errors_dir = Path("xml_errors")
        self.xml_errors_dir.mkdir(exist_ok=True)

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
            # Check if it's an actions response
            if 'actions' in response and isinstance(response.get('actions'), list):
                return {
                    'type': 'actions',
                    'content': response
                }
            # Otherwise treat as generic JSON
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
                # Check if it's an actions response
                if 'actions' in json_content and isinstance(json_content.get('actions'), list):
                    return {
                        'type': 'actions',
                        'content': json_content
                    }
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

            # Handle multiple root elements by wrapping in a container
            # API may return <stages>...</stages><focus>...</focus>
            # which is invalid XML (only one root allowed)
            if xml_string.count('<?xml') <= 1:  # Not already wrapped
                # Check if there are multiple root elements
                import re
                # Find all root-level tags
                root_tags = re.findall(r'<(\w+)(?:\s|>)', xml_string)
                # Check if first root tag appears twice (opening and closing)
                if len(root_tags) > 1:
                    first_tag = root_tags[0]
                    # Count occurrences of this tag at root level
                    root_pattern = rf'^<{first_tag}[\s>].*?</{first_tag}>.*?^<\w+'
                    if re.search(r'</\w+>\s*<\w+', xml_string):
                        # Multiple root elements detected, wrap them
                        xml_string = f'<response>{xml_string}</response>'
                        self.info("[Parser] Wrapped multiple root elements in <response> container")

            root = ET.fromstring(xml_string)

            # If wrapped in <response>, unwrap it but keep reference to wrapper
            wrapper = None
            if root.tag == 'response':
                wrapper = root
                # Find the actual content element
                stages_elem = root.find('stages')
                steps_elem = root.find('steps')
                behavior_elem = root.find('behavior')
                reflection_elem = root.find('reflection')

                if stages_elem is not None:
                    root = stages_elem
                elif steps_elem is not None:
                    root = steps_elem
                elif behavior_elem is not None:
                    root = behavior_elem
                elif reflection_elem is not None:
                    root = reflection_elem

            # Check root tag to determine content type
            if root.tag == 'stages':
                return {
                    'type': 'stages',
                    'content': self._parse_stages_xml(root, wrapper)
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
            elif root.tag == 'reflection':
                return {
                    'type': 'reflection',
                    'content': self._parse_reflection_xml(root)
                }
            else:
                self.warning(f"Unknown XML root tag: {root.tag}")
                return {
                    'type': 'xml',
                    'content': xml_string
                }
        except ET.ParseError as e:
            self.error(f"XML parse error: {e}")
            # Save detailed error log
            self._save_xml_error_log(xml_string, e)
            return {
                'type': 'unknown',
                'content': xml_string
            }

    def _parse_stages_xml(self, root: ET.Element, wrapper: ET.Element = None) -> Dict[str, Any]:
        """
        Parse <stages> XML definition.

        Args:
            root: <stages> element
            wrapper: Optional wrapper element (e.g., <response>) that may contain <focus>

        Returns:
            Dict with stages list and focus
        """
        stages = []
        focus = ""

        for child in root:
            if child.tag == 'stage':
                # Direct <stage> child
                stage = self._parse_stage_element(child)
                stages.append(stage)
            elif child.tag in ['remaining', 'completed', 'current']:
                # Stages wrapped in <remaining>, <completed>, or <current>
                for stage_elem in child.findall('stage'):
                    stage = self._parse_stage_element(stage_elem)
                    stages.append(stage)
            elif child.tag == 'focus':
                # Clean up whitespace
                focus = (child.text or "").strip()

        # If focus not found in stages element, check wrapper
        if not focus and wrapper is not None:
            focus_elem = wrapper.find('focus')
            if focus_elem is not None:
                focus = (focus_elem.text or "").strip()

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

    def _parse_reflection_xml(self, root: ET.Element) -> Dict[str, Any]:
        """
        Parse <reflection> XML definition.

        Returns:
            Dict with reflection details including:
            - behavior_is_complete: boolean from attribute
            - next_state: target FSM state
            - variables_produced: dict of new variables
            - artifacts_produced: list of completed artifacts
            - outputs_tracking: dict with produced/in_progress/remaining
            - context_for_next: dict with whathappened and recommendations
        """
        reflection = {
            'behavior_is_complete': root.get('current_step_is_complete', '').lower() == 'true',
            'next_state': None,
            'variables_produced': {},
            'artifacts_produced': [],
            'outputs_tracking': {
                'produced': [],
                'in_progress': [],
                'remaining': []
            },
            'context_for_next': {
                'whathappened': {},
                'recommendations_for_next': {}
            }
        }

        for child in root:
            if child.tag == 'decision':
                # Extract next_state from decision
                next_state_elem = child.find('next_state')
                if next_state_elem is not None and next_state_elem.text:
                    reflection['next_state'] = next_state_elem.text.strip()

            elif child.tag == 'context_for_next':
                # Extract variables_produced
                vars_elem = child.find('variables_produced')
                if vars_elem is not None:
                    for var in vars_elem.findall('variable'):
                        name = var.get('name')
                        value = var.get('value', var.text or '')
                        if name:
                            reflection['variables_produced'][name] = value

                # Extract whathappened
                whathappened_elem = child.find('whathappened')
                if whathappened_elem is not None:
                    overview_elem = whathappened_elem.find('overview')
                    if overview_elem is not None and overview_elem.text:
                        reflection['context_for_next']['whathappened']['overview'] = overview_elem.text.strip()

                    key_findings_elem = whathappened_elem.find('key_findings')
                    if key_findings_elem is not None and key_findings_elem.text:
                        reflection['context_for_next']['whathappened']['key_findings'] = key_findings_elem.text.strip()

                # Extract recommendations_for_next
                recommendations_elem = child.find('recommendations_for_next')
                if recommendations_elem is not None:
                    if_continuing_elem = recommendations_elem.find('if_continuing_behavior')
                    if if_continuing_elem is not None and if_continuing_elem.text:
                        reflection['context_for_next']['recommendations_for_next']['if_continuing_behavior'] = if_continuing_elem.text.strip()

                    if_moving_forward_elem = recommendations_elem.find('if_moving_forward')
                    if if_moving_forward_elem is not None and if_moving_forward_elem.text:
                        reflection['context_for_next']['recommendations_for_next']['if_moving_forward'] = if_moving_forward_elem.text.strip()

            elif child.tag == 'evaluation':
                # Extract artifacts_produced
                artifacts_elem = child.find('artifacts_produced')
                if artifacts_elem is not None:
                    for artifact in artifacts_elem.findall('artifact'):
                        artifact_name = artifact.get('name')
                        artifact_status = artifact.get('status', 'unknown')
                        if artifact_name:
                            reflection['artifacts_produced'].append({
                                'name': artifact_name,
                                'status': artifact_status
                            })

            elif child.tag == 'outputs_tracking_update':
                # Extract produced/in_progress/remaining outputs
                produced_elem = child.find('produced')
                if produced_elem is not None:
                    for artifact in produced_elem.findall('artifact'):
                        if artifact.text:
                            reflection['outputs_tracking']['produced'].append(artifact.text.strip())

                in_progress_elem = child.find('in_progress')
                if in_progress_elem is not None:
                    for artifact in in_progress_elem.findall('artifact'):
                        if artifact.text:
                            reflection['outputs_tracking']['in_progress'].append(artifact.text.strip())

                remaining_elem = child.find('remaining')
                if remaining_elem is not None:
                    for artifact in remaining_elem.findall('artifact'):
                        if artifact.text:
                            reflection['outputs_tracking']['remaining'].append(artifact.text.strip())

        return reflection

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

    def _save_xml_error_log(self, xml_string: str, error: ET.ParseError) -> None:
        """
        Save detailed XML parsing error log with context and suggestions.

        Args:
            xml_string: The XML content that failed to parse
            error: The ParseError exception
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        error_file = self.xml_errors_dir / f"xml_error_{timestamp}.log"

        # Parse error details
        error_msg = str(error)
        line_num = None
        col_num = None

        # Extract line and column from error message
        # Format: "not well-formed (invalid token): line 45, column 47"
        import re
        match = re.search(r'line (\d+), column (\d+)', error_msg)
        if match:
            line_num = int(match.group(1))
            col_num = int(match.group(2))

        # Split XML into lines for context display
        xml_lines = xml_string.split('\n')

        # Generate error report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("XML PARSING ERROR REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append(f"Timestamp: {datetime.now().isoformat()}")
        report_lines.append(f"Error Type: {type(error).__name__}")
        report_lines.append(f"Error Message: {error_msg}")
        report_lines.append("")

        if line_num and col_num:
            report_lines.append(f"Error Location: Line {line_num}, Column {col_num}")
            report_lines.append("")

            # Show context (5 lines before and after)
            context_start = max(0, line_num - 6)
            context_end = min(len(xml_lines), line_num + 5)

            report_lines.append("-" * 80)
            report_lines.append("ERROR CONTEXT (with line numbers):")
            report_lines.append("-" * 80)

            for i in range(context_start, context_end):
                line = xml_lines[i]
                line_marker = ">>> " if i == line_num - 1 else "    "
                report_lines.append(f"{line_marker}{i+1:4d} | {line}")

                # Add pointer to error column
                if i == line_num - 1 and col_num:
                    pointer = " " * (len(line_marker) + 7 + col_num - 1) + "^"
                    report_lines.append(pointer + " ERROR HERE")

            report_lines.append("-" * 80)
            report_lines.append("")

        # Add diagnostic information
        report_lines.append("DIAGNOSTIC ANALYSIS:")
        report_lines.append("-" * 80)

        # Check for common XML errors
        diagnostics = self._analyze_xml_error(xml_string, error_msg, line_num, col_num, xml_lines)
        for diagnostic in diagnostics:
            report_lines.append(f"• {diagnostic}")

        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("FULL XML CONTENT:")
        report_lines.append("-" * 80)
        report_lines.append(xml_string)
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("END OF ERROR REPORT")
        report_lines.append("=" * 80)

        # Write to file
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        self.warning(f"⚠️  XML error details saved to: {error_file}")

    def _analyze_xml_error(self, xml_string: str, error_msg: str,
                          line_num: Optional[int], col_num: Optional[int],
                          xml_lines: List[str]) -> List[str]:
        """
        Analyze XML error and provide diagnostic suggestions.

        Returns:
            List of diagnostic messages and suggestions
        """
        diagnostics = []

        # Check for common patterns
        if "not well-formed" in error_msg.lower():
            diagnostics.append("XML is not well-formed. Common causes:")
            diagnostics.append("  - Special characters (<, >, &) not properly escaped")
            diagnostics.append("  - Missing closing tags")
            diagnostics.append("  - Invalid characters in attribute values")

        if "mismatched tag" in error_msg.lower():
            diagnostics.append("Mismatched XML tags detected. Check that:")
            diagnostics.append("  - Every opening tag has a matching closing tag")
            diagnostics.append("  - Tag names are spelled correctly")
            diagnostics.append("  - Tags are properly nested")

            # Try to find the mismatched tag
            if line_num and line_num <= len(xml_lines):
                error_line = xml_lines[line_num - 1]
                import re
                # Look for closing tag
                closing_match = re.search(r'</(\w+)>', error_line)
                if closing_match:
                    closing_tag = closing_match.group(1)
                    diagnostics.append(f"  - Found closing tag: </{closing_tag}>")
                    diagnostics.append(f"  - Search for matching opening tag: <{closing_tag}>")

        if "invalid token" in error_msg.lower():
            diagnostics.append("Invalid token found. This usually means:")
            diagnostics.append("  - Unescaped special characters in text content")
            diagnostics.append("  - Illegal characters in tag names or attributes")
            diagnostics.append("  - Malformed XML structure")

        # Check for unclosed tags
        import re
        opening_tags = re.findall(r'<(\w+)[\s>]', xml_string)
        closing_tags = re.findall(r'</(\w+)>', xml_string)

        from collections import Counter
        opening_count = Counter(opening_tags)
        closing_count = Counter(closing_tags)

        unclosed = []
        for tag, count in opening_count.items():
            if closing_count.get(tag, 0) < count:
                unclosed.append(f"{tag} (missing {count - closing_count.get(tag, 0)} closing tag(s))")

        if unclosed:
            diagnostics.append("")
            diagnostics.append("Potentially unclosed tags:")
            for tag in unclosed:
                diagnostics.append(f"  - <{tag}>")

        # Check for unescaped characters
        if line_num and line_num <= len(xml_lines):
            error_line = xml_lines[line_num - 1]
            # Look for unescaped characters in what should be text content
            if re.search(r'>[^<]*[<>&][^<]*<', error_line):
                diagnostics.append("")
                diagnostics.append("Possible unescaped special characters in text content:")
                diagnostics.append("  - '<' should be '&lt;'")
                diagnostics.append("  - '>' should be '&gt;'")
                diagnostics.append("  - '&' should be '&amp;'")

        # Suggest fixes
        diagnostics.append("")
        diagnostics.append("SUGGESTED FIXES:")
        diagnostics.append("  1. Review the API/LLM prompt to ensure valid XML output")
        diagnostics.append("  2. Add XML validation in the API response generation")
        diagnostics.append("  3. Consider adding XML repair logic in the client")
        diagnostics.append("  4. Use CDATA sections for text with special characters")

        return diagnostics


# Create singleton instance
response_parser = ResponseParser()
