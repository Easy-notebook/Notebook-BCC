#!/usr/bin/env python3
"""
Test script to verify that context_for_next is properly extracted and saved to state.
"""

import json
import xml.etree.ElementTree as ET
from utils.response_parser import ResponseParser

# Sample XML response with context_for_next
sample_xml = """<reflection current_step_is_complete="false">
  <evaluation>
    <artifacts_produced>
      <artifact name="data_inventory" status="missing">No inventory summary for the dataset has been saved or produced.</artifact>
      <artifact name="initial_data_catalog" status="missing">No catalog file containing metadata descriptions has been created.</artifact>
    </artifacts_produced>
    <acceptance_validation>
      <criterion status="failed">data_inventory.shape[0] > 0</criterion>
      <criterion status="failed">os.path.exists('initial_data_catalog.json') == True</criterion>
    </acceptance_validation>
    <execution_quality>
      <code_execution>success</code_execution>
      <errors_found>No runtime errors or exceptions during code execution. Outputs were printed but not saved.</errors_found>
    </execution_quality>
    <goal_achievement>
      <status>not_achieved</status>
      <reasoning>The initial dataset inventory and metadata catalog artifacts were not generated or stored as files, preventing the fulfillment of the current step's goal.</reasoning>
    </goal_achievement>
  </evaluation>

  <decision>
    <next_state>STEP_RUNNING</next_state>
    <reasoning>The step is incomplete because neither required artifacts have been produced, and acceptance criteria have not been met. Iteration is needed to ensure output files are saved correctly and criteria alignment is achieved.</reasoning>
  </decision>

  <context_for_next>
    <variables_produced></variables_produced>
    <whathappened>
      <overview>Initial exploration confirmed the dataset is loaded and valid, with 2930 rows and 82 columns. Some inventory-related information was printed but has not been saved or cataloged.</overview>
      <key_findings>The dataset contains diverse data types and significant missing values in several columns (i.e., Alley, Pool QC). Printed statistics include row/column counts, data types, and basic statistics.</key_findings>
    </whathappened>
    <recommendations_for_next>
      <if_continuing_behavior>Ensure both data inventory (`data_inventory.json`) and metadata catalog (`initial_data_catalog.json`) artifacts are generated and saved as files. Validate files against their respective acceptance criteria.</if_continuing_behavior>
      <if_moving_forward>N/A, as current step completion is required before advancing to the next step.</if_moving_forward>
    </recommendations_for_next>
  </context_for_next>

  <outputs_tracking_update>
    <produced></produced>
    <in_progress><artifact>data_inventory</artifact><artifact>initial_data_catalog</artifact></in_progress>
    <remaining><artifact>data_inventory</artifact><artifact>initial_data_catalog</artifact></remaining>
  </outputs_tracking_update>
</reflection>"""


def main():
    print("=" * 80)
    print("Testing context_for_next extraction")
    print("=" * 80)

    # Create parser
    parser = ResponseParser()

    # Parse the XML
    print("\n1. Parsing XML response...")
    parsed = parser.parse_response(sample_xml)
    result = parsed.get('content', {})

    # Display parsed results
    print("\n2. Parsed reflection data:")
    print(json.dumps(result, indent=2))

    # Check if context_for_next was extracted
    print("\n3. Verification:")
    print("-" * 80)

    if 'context_for_next' in result:
        context = result['context_for_next']
        print("✓ context_for_next field exists")

        if 'whathappened' in context:
            print("✓ whathappened field exists")
            whathappened = context['whathappened']

            if 'overview' in whathappened:
                print(f"✓ overview extracted: {whathappened['overview'][:50]}...")
            else:
                print("✗ overview NOT found")

            if 'key_findings' in whathappened:
                print(f"✓ key_findings extracted: {whathappened['key_findings'][:50]}...")
            else:
                print("✗ key_findings NOT found")
        else:
            print("✗ whathappened field NOT found")

        if 'recommendations_for_next' in context:
            print("✓ recommendations_for_next field exists")
            recommendations = context['recommendations_for_next']

            if 'if_continuing_behavior' in recommendations:
                print(f"✓ if_continuing_behavior extracted: {recommendations['if_continuing_behavior'][:50]}...")
            else:
                print("✗ if_continuing_behavior NOT found")

            if 'if_moving_forward' in recommendations:
                print(f"✓ if_moving_forward extracted: {recommendations['if_moving_forward'][:50]}...")
            else:
                print("✗ if_moving_forward NOT found")
        else:
            print("✗ recommendations_for_next field NOT found")
    else:
        print("✗ context_for_next field NOT found in result")

    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
