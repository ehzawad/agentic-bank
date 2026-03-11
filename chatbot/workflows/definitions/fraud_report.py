from chatbot.workflows.models import WorkflowDefinition, WorkflowStep, StepType, SlotSpec

fraud_report = WorkflowDefinition(
    workflow_id="fraud_report",
    name="Fraud Report",
    steps=[
        WorkflowStep(
            step_id="block_card",
            step_type=StepType.PROACTIVE,
            description="Block the compromised card immediately",
            tool_to_call="block_card",
        ),
        WorkflowStep(
            step_id="collect_dispute_details",
            step_type=StepType.NEEDS_INPUT,
            description="Collect dispute details",
            slots_needed=[
                SlotSpec(name="card_possession", description="whether customer has card in hand, lost, or stolen"),
                SlotSpec(name="last_authorized_use", description="last transaction the customer made"),
            ],
        ),
        WorkflowStep(
            step_id="file_dispute",
            step_type=StepType.AUTO,
            description="File the dispute for unauthorized transactions",
            tool_to_call="file_dispute",
        ),
        WorkflowStep(
            step_id="order_replacement",
            step_type=StepType.PROACTIVE,
            description="Offer and order a replacement card",
            tool_to_call="order_replacement_card",
        ),
    ],
)
