"""
Lightweight XML Parser for Planning API
Only handles stages/steps/behaviors XML definitions from Planning API.

Note: Reflecting API uses action stream (NDJSON), not XML.
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Union, Optional
from silantui import ModernLogger


class PlanningXMLParser(ModernLogger):
    """
    Lightweight parser for Planning API XML responses.

    Handles:
    - <stages> - Workflow stages definition
    - <steps> - Step definitions for a stage
    - <behavior> - Behavior definition
    """

    def __init__(self):
        super().__init__("PlanningXMLParser")

    def parse(self, response: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse Planning API response.

        Args:
            response: XML string or already-parsed dict

        Returns:
            Parsed content dict
        """
        # If already dict, return as-is
        if isinstance(response, dict):
            return response

        # If string, try to parse as XML or JSON
        if isinstance(response, str):
            response = response.strip()

            # Check if XML
            if response.startswith('<'):
                return self._parse_xml(response)

            # Try JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                self.error(f"Failed to parse response: {response[:100]}")
                raise ValueError(f"Cannot parse response as XML or JSON")

        raise ValueError(f"Unsupported response type: {type(response)}")

    def _parse_xml(self, xml_string: str) -> Dict[str, Any]:
        """Parse XML response."""
        try:
            # Preprocess XML to handle special characters
            xml_string = self._preprocess_xml(xml_string)

            root = ET.fromstring(xml_string)

            if root.tag == 'workflow':
                return self._parse_workflow(root)
            elif root.tag == 'stages':
                return self._parse_stages(root)
            elif root.tag == 'steps':
                return self._parse_steps(root)
            elif root.tag == 'behavior':
                return self._parse_behavior(root)
            else:
                self.warning(f"Unknown XML root tag: {root.tag}")
                return {}

        except ET.ParseError as e:
            self.error(f"XML parse error: {e}")
            self._save_xml_error(xml_string, e)

            # Try to recover partial XML by completing it
            if "no element found" in str(e):
                self.warning("Attempting to recover from incomplete XML...")
                recovered = self._try_recover_incomplete_xml(xml_string)
                if recovered:
                    self.info("Successfully recovered partial XML")
                    return recovered

            raise ValueError(f"Invalid XML: {e}")

    def _parse_workflow(self, root: ET.Element) -> Dict[str, Any]:
        """Parse <workflow> XML (new structure for IDLE state)."""
        result = {}

        for child in root:
            if child.tag == 'title':
                result['title'] = (child.text or "").strip()
            elif child.tag == 'description':
                result['description'] = (child.text or "").strip()
            elif child.tag == 'stages':
                # Parse the stages element
                stages_data = self._parse_stages(child)
                result.update(stages_data)

        return result

    def _parse_stages(self, root: ET.Element) -> Dict[str, Any]:
        """Parse <stages> XML."""
        stages = []
        focus = ''
        title = ''
        description = ''

        for child in root:
            if child.tag == 'title':
                # Extract notebook title (legacy support)
                title = (child.text or "").strip()
            elif child.tag == 'description':
                # Extract notebook description (legacy support)
                description = (child.text or "").strip()
            elif child.tag == 'remaining':
                # Stages are inside <remaining> wrapper (legacy support)
                for stage_elem in child:
                    if stage_elem.tag == 'stage':
                        stage = self._parse_stage_element(stage_elem)
                        stages.append(stage)
            elif child.tag == 'stage':
                # Direct stage element (new structure & legacy support)
                stage = self._parse_stage_element(child)
                stages.append(stage)
            elif child.tag == 'focus':
                # Extract focus text
                focus = (child.text or "").strip()

        result = {'stages': stages}
        if title:
            result['title'] = title
        if description:
            result['description'] = description
        if focus:
            result['focus'] = focus
        return result

    def _parse_stage_element(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse a single <stage> element."""
        stage = {
            'stage_id': elem.get('id'),
            'title': elem.get('title', ''),
            'goal': '',
            'verified_artifacts': {},
            'required_variables': {}
        }

        # Handle optional positioning attributes
        if elem.get('insert_before'):
            stage['insert_before'] = elem.get('insert_before')
        if elem.get('insert_after'):
            stage['insert_after'] = elem.get('insert_after')
        if elem.get('replaces'):
            stage['replaces'] = elem.get('replaces')
        if elem.get('optional'):
            stage['optional'] = elem.get('optional') in ['true', 'True', '1']

        for child in elem:
            if child.tag == 'goal':
                stage['goal'] = (child.text or "").strip()
            elif child.tag == 'verified_artifacts':
                stage['verified_artifacts'] = self._parse_variables(child)
            elif child.tag == 'required_variables':
                stage['required_variables'] = self._parse_variables(child)

        return stage

    def _parse_steps(self, root: ET.Element) -> Dict[str, Any]:
        """Parse <steps> XML."""
        steps = []
        focus = ''

        for child in root:
            if child.tag == 'remaining':
                # Steps are inside <remaining> wrapper
                for step_elem in child:
                    if step_elem.tag == 'step':
                        step = self._parse_step_element(step_elem)
                        steps.append(step)
            elif child.tag == 'step':
                # Direct step element (legacy support)
                step = self._parse_step_element(child)
                steps.append(step)
            elif child.tag == 'focus':
                # Extract focus text
                focus = (child.text or "").strip()

        result = {'steps': steps}
        if focus:
            result['focus'] = focus
        return result

    def _parse_step_element(self, elem: ET.Element) -> Dict[str, Any]:
        """Parse a single <step> element."""
        step = {
            'step_id': elem.get('id'),
            'title': elem.get('title', ''),
            'goal': '',
            'verified_artifacts': {},
            'required_variables': {}
        }

        for child in elem:
            if child.tag == 'goal':
                step['goal'] = (child.text or "").strip()
            elif child.tag == 'verified_artifacts':
                step['verified_artifacts'] = self._parse_variables(child)
            elif child.tag == 'required_variables':
                step['required_variables'] = self._parse_variables(child)

        return step

    def _parse_behavior(self, root: ET.Element) -> Dict[str, Any]:
        """Parse <behavior> XML."""
        behavior = {
            'behavior_id': root.get('id'),
            'step_id': root.get('step_id'),
            'agent': '',
            'task': '',
            'inputs': {},
            'outputs': {},
            'acceptance': []
        }

        for child in root:
            if child.tag == 'agent':
                behavior['agent'] = child.text or ""
            elif child.tag == 'task':
                behavior['task'] = child.text or ""
            elif child.tag == 'inputs':
                behavior['inputs'] = self._parse_variables(child)
            elif child.tag == 'outputs':
                behavior['outputs'] = self._parse_outputs(child)
            elif child.tag == 'acceptance':
                behavior['acceptance'] = self._parse_acceptance(child)

        return behavior

    def _parse_variables(self, element: ET.Element) -> Dict[str, str]:
        """Parse variable definitions."""
        variables = {}
        for var in element.findall('variable'):
            name = var.get('name')
            value = (var.text or "").strip()
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

    def _parse_acceptance(self, element: ET.Element) -> list:
        """Parse acceptance criteria."""
        criteria = []
        for criterion in element.findall('criterion'):
            if criterion.text:
                criteria.append(criterion.text.strip())
        return criteria

    def _preprocess_xml(self, xml_string: str) -> str:
        """
        Preprocess XML to handle special characters and malformed attributes.

        Fixes:
        1. Escapes special chars (<, >, &) in text content
        2. Fixes boolean attributes without values (e.g., "optional" → "optional='true'")
        """
        # First pass: Fix boolean attributes without values
        xml_string = self._fix_boolean_attributes(xml_string)

        # Second pass: Repair obvious mismatched closing tags from the API
        xml_string = self._fix_mismatched_tags(xml_string)

        # Third pass: Escape special characters in text content
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

    def _fix_mismatched_tags(self, xml_string: str) -> str:
        """Automatically correct common closing-tag typos from the API."""
        import re

        tag_pattern = re.compile(r'<(/?)([A-Za-z0-9_:-]+)([^>]*)>')
        result = []
        last_index = 0
        stack = []

        for match in tag_pattern.finditer(xml_string):
            start, end = match.span()
            result.append(xml_string[last_index:start])

            slash, name, remainder = match.groups()
            token = match.group(0)

            if slash:
                if stack:
                    expected = stack[-1]
                    if name != expected:
                        line = xml_string.count('\n', 0, start) + 1
                        self.warning(
                            f"Fixing mismatched closing tag </{name}> at line {line}, expected </{expected}>"
                        )
                        token = f"</{expected}>"
                    stack.pop()
            else:
                is_self_closing = token.rstrip().endswith('/>')
                if not is_self_closing:
                    stack.append(name)

            result.append(token)
            last_index = end

        result.append(xml_string[last_index:])
        return ''.join(result)

    def _try_recover_incomplete_xml(self, xml_string: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover from incomplete XML by closing unclosed tags.

        This handles cases where API response was truncated mid-stream.
        """
        lines = xml_string.strip().split('\n')

        # Track open tags
        tag_stack = []
        for line in lines:
            # Find opening tags
            import re
            open_tags = re.findall(r'<(\w+)[\s>]', line)
            close_tags = re.findall(r'</(\w+)>', line)

            for tag in open_tags:
                # Skip self-closing or already-closed tags
                if f'<{tag}' in line and '/>' in line:
                    continue
                tag_stack.append(tag)

            for tag in close_tags:
                if tag_stack and tag_stack[-1] == tag:
                    tag_stack.pop()

        # Close unclosed tags
        if tag_stack:
            self.warning(f"Incomplete XML detected. Unclosed tags: {tag_stack}")

            # Add closing tags in reverse order
            closing_tags = []
            for tag in reversed(tag_stack):
                closing_tags.append(f"</{tag}>")

            completed_xml = xml_string.strip() + '\n' + '\n'.join(closing_tags)

            # Try to parse the completed XML
            try:
                completed_xml = self._preprocess_xml(completed_xml)
                root = ET.fromstring(completed_xml)

                self.info(f"✅ Recovered XML by closing tags: {tag_stack}")

                if root.tag == 'workflow':
                    result = self._parse_workflow(root)
                    result['_warning'] = 'Recovered from incomplete API response'
                    return result
                elif root.tag == 'stages':
                    result = self._parse_stages(root)
                    # Add warning to result
                    result['_warning'] = 'Recovered from incomplete API response'
                    return result
                elif root.tag == 'steps':
                    result = self._parse_steps(root)
                    result['_warning'] = 'Recovered from incomplete API response'
                    return result
                elif root.tag == 'behavior':
                    result = self._parse_behavior(root)
                    result['_warning'] = 'Recovered from incomplete API response'
                    return result

            except Exception as recovery_error:
                self.error(f"Recovery attempt failed: {recovery_error}")
                return None

        return None

    def _fix_boolean_attributes(self, xml_string: str) -> str:
        """
        Fix boolean attributes without values.

        Examples:
        - <stage optional> → <stage optional="true">
        - <step required> → <step required="true">
        """
        import re

        # Pattern: attribute name followed by whitespace and then > or another attribute
        # Matches: optional> or optional attr=
        pattern = r'\b(optional|required|disabled|enabled|hidden)\s*([>\s])'

        def replacer(match):
            attr_name = match.group(1)
            following = match.group(2)
            return f'{attr_name}="true"{following}'

        return re.sub(pattern, replacer, xml_string)

    def _save_xml_error(self, xml_string: str, error: ET.ParseError) -> None:
        """Save XML parsing error for debugging."""
        from pathlib import Path
        from datetime import datetime

        xml_errors_dir = Path("xml_errors")
        xml_errors_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        error_file = xml_errors_dir / f"xml_error_{timestamp}.log"

        # Parse error details
        error_msg = str(error)

        # Extract line and column from error message
        import re
        line_num = None
        col_num = None
        match = re.search(r'line (\d+), column (\d+)', error_msg)
        if match:
            line_num = int(match.group(1))
            col_num = int(match.group(2))

        # Generate error report
        report = [
            "=" * 80,
            "XML PARSING ERROR REPORT",
            "=" * 80,
            "",
            f"Timestamp: {datetime.now().isoformat()}",
            f"Error: {error_msg}",
            ""
        ]

        if line_num and col_num:
            xml_lines = xml_string.split('\n')
            report.append(f"Error Location: Line {line_num}, Column {col_num}")
            report.append("")
            report.append("-" * 80)
            report.append("ERROR CONTEXT:")
            report.append("-" * 80)

            # Show context (5 lines before and after)
            context_start = max(0, line_num - 6)
            context_end = min(len(xml_lines), line_num + 5)

            for i in range(context_start, context_end):
                line = xml_lines[i]
                marker = ">>> " if i == line_num - 1 else "    "
                report.append(f"{marker}{i+1:4d} | {line}")

                # Add pointer to error column
                if i == line_num - 1 and col_num:
                    pointer = " " * (len(marker) + 7 + col_num - 1) + "^"
                    report.append(pointer + " ERROR HERE")

            report.append("-" * 80)
            report.append("")

        report.append("-" * 80)
        report.append("FULL XML CONTENT:")
        report.append("-" * 80)
        report.append(xml_string)
        report.append("")
        report.append("=" * 80)

        # Write to file
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        self.warning(f"XML error details saved to: {error_file}")


# Singleton instance
planning_xml_parser = PlanningXMLParser()
