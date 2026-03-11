from chatbot.workflows.models import WorkflowDefinition, WorkflowStep, StepType, SlotSpec

international_transfer = WorkflowDefinition(
    workflow_id="international_transfer",
    name="International Wire Transfer",
    steps=[
        WorkflowStep(
            step_id="collect_recipient",
            step_type=StepType.NEEDS_INPUT,
            description="Collect recipient banking details",
            slots_needed=[
                SlotSpec(name="recipient_name", description="full name on recipient's bank account"),
                SlotSpec(name="recipient_bank", description="name of recipient's bank"),
                SlotSpec(name="sort_code", description="sort code or routing number"),
                SlotSpec(name="account_number", description="recipient's account number"),
                SlotSpec(name="recipient_address", description="recipient's address"),
                SlotSpec(name="purpose", description="reason for transfer (family_support, gift, education, medical, business, other)"),
            ],
        ),
        WorkflowStep(
            step_id="confirm",
            step_type=StepType.CONFIRM,
            description="Show transfer summary and get confirmation",
        ),
        WorkflowStep(
            step_id="execute",
            step_type=StepType.AUTO,
            description="Execute the wire transfer",
            tool_to_call="initiate_transfer",
        ),
    ],
)
