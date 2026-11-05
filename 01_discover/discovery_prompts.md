# Discovery prompt collection

These prompts are for your own research with an AI assistant. They are written so that the assistant has to show its working. Replace the text in angle brackets. Paste the answer into `research_log.md` with the date and what you verified.

## Understanding the domain

```
You are a warehouse operations manager at a distribution centre with six dock doors receiving 190 to 240 appointments a day.
Explain, in plain language a new graduate can follow, what happens between a truck arriving at the gate and leaving the facility.
List the five most common reasons a booked appointment becomes infeasible, and for each say which system would know about it first.
Cite the industry term for each stage.
```

## Pushing a why deeper

```
A driver reports "tyre damaged near Neemrana, 45 minutes to repair". A coordinator rebooks the dock slot by phone.
Give me three candidate root causes for why this takes a coordinator 20 minutes instead of 2, ranked by how likely each is.
For each candidate, name one piece of data that would confirm or refute it.
Do not propose solutions yet.
```

## Checking a claim before you repeat it

```
I believe that showing a driver an available slot and reserving it for them are the same thing. Argue against this belief using a concrete scenario with two drivers and one dock. Then say what state a slot must carry for the difference to be safe.
```

## Finding what the data can and cannot answer

```
Here is a data dictionary: <paste data/skyways_data_dictionary.csv>.
I want to answer the question "<your question>". Write the SQL, state which columns you rely on, and list what the data cannot tell me about this question.
```

## Interrogating your own design

```
Here is my proposed design in one paragraph: <paragraph>.
Act as a sceptical warehouse planner. Ask me the five questions you would ask before trusting this system with your dock schedule. Rank them by how embarrassing an unanswered one would be in a demo.
```

## Research moves that pair with these prompts

| Move | What you do | What you keep |
|---|---|---|
| Vendor scan | Watch one dock-scheduling product demo and list its features | A features table with "we build", "we fake", "out of scope" columns |
| Paper skim | Read the abstract and the figures of one scheduling paper | One sentence on what the paper decides and one on what it ignores |
| Data probe | Run three queries against the database that test your root cause | The queries and their row counts |
| Driver voice | Read all 148 labelled messages once | The five messages your design would get wrong |
