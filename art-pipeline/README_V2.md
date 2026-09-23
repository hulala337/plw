# Art Pipeline V2

V2 adds Character Bible, reference-image management, dependency-aware production queues and reference-driven generation.

Reference folders:
art-work/references/pelican/
art-work/references/office/

Check references:
python art-pipeline/reference_manager.py --check

Build queue:
python art-pipeline/task_queue.py

Generate a reference-driven asset:
python art-pipeline/prompt_builder.py --ids B01
python art-pipeline/generate_with_reference.py --id B01 --reference art-work/references/pelican/master-reference.png

After B01 is approved, use that approved master as the identity reference for later character states.

The reference workflow is deliberately separate from ordinary generation so the style anchor can be reviewed before scaling to dozens of assets.
