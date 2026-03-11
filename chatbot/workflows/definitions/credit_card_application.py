from chatbot.workflows.models import WorkflowDefinition, WorkflowStep, StepType, SlotSpec

credit_card_application = WorkflowDefinition(
    workflow_id="credit_card_application",
    name="Credit Card Application",
    steps=[
        WorkflowStep(
            step_id="confirm_details",
            step_type=StepType.NEEDS_INPUT,
            description="Confirm personal details (name, address)",
            slots_needed=[
                SlotSpec(name="address_confirmed", description="whether address on file is current"),
            ],
        ),
        WorkflowStep(
            step_id="collect_income",
            step_type=StepType.NEEDS_INPUT,
            description="Collect income and employment information",
            slots_needed=[
                SlotSpec(name="annual_income", description="annual income in USD"),
                SlotSpec(name="employment_status", description="employed, self-employed, retired, etc."),
            ],
        ),
        WorkflowStep(
            step_id="collect_ssn",
            step_type=StepType.NEEDS_INPUT,
            description="Collect SSN last 4 digits",
            slots_needed=[
                SlotSpec(name="ssn_last4", description="last 4 digits of Social Security Number"),
            ],
        ),
        WorkflowStep(
            step_id="submit",
            step_type=StepType.AUTO,
            description="Submit the credit card application",
            tool_to_call="submit_credit_application",
        ),
    ],
)
