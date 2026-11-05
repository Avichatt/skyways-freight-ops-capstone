# Questions the panel asks, and what a good answer contains

| Question | A weak answer | A good answer contains |
|---|---|---|
| Why this pain point? | "It seemed interesting" | The Five Whys chain, the matrix score, the number |
| Walk me through the architecture | Reads the boxes | Names what each box owns and the one decision that shaped it |
| How does the agent know a slot is free? | "It checks the database" | The feasibility rules, the view used, the difference between open and available |
| What stops a double booking? | "The code checks first" | The unique index, the transaction, the test, the replay output |
| How did you evaluate the model? | "Accuracy was 92 percent" | The baseline, the time-ordered split, the metric in minutes, where it fails |
| What did you not build? | Silence | Three named limits and the enterprise-grade version of each |
| What was the hardest bug? | "Nothing major" | A specific moment, what you saw, what you changed |
| What would you do with another month? | A feature list | One improvement, its effort, and why it comes first |
| What did the LLM get wrong? | "It was mostly fine" | A case from eval_cases.jsonl that failed first and the prompt or tool change that fixed it |
| How much did a conversation cost? | Unknown | Tokens per turn times price, and the monthly estimate at 300 exceptions a day |
