# Resume bullets

Formula: Verb + what you built + for whom + measurable outcome + how (tools). One line each. Numbers from your repository only.

Examples to adapt (replace the numbers with yours)

- Built a tool-calling conversational agent (LangGraph, OpenRouter, SQLite) that converts free-text truck-driver delay messages into feasible, held dock appointments; 12 of 12 evaluation conversations pass, including a concurrent-request case with zero double bookings.
- Designed the slot commitment state machine (shown, held, requested, confirmed) and enforced it with a database partial unique index, proven by a multi-threaded test.
- Trained a gradient-boosted regressor on 6,000 dock visits to predict unload duration; cut median absolute error from 14 minutes (dock-type median baseline) to 7 minutes on a time-ordered test split, enabling 15-minute slot buffers instead of 30.
- Ran a Five Whys root-cause analysis on dock coordination delays and traced the root cause through four operational tables before writing a line of code.

How to talk about it in an interview (30 seconds)
"The business problem was [one sentence]. I found the root cause was [one sentence]. I built [one sentence]. The thing I am proudest of is [the proof]. If I had another month I would [next step]."

Questions you should be ready for
- What happens when two drivers pick the same slot in the same second?
- Why is a shown slot not a reserved slot?
- How do you know your model is not leaking future information?
- What does the agent refuse to do, and how did you test that?
- What did the data not tell you?
