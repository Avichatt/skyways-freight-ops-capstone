# Five Whys worksheet

Fill one worksheet per pain point you are considering. Three worksheets is a good number; one is too few, because the first pain point you notice is almost never the deepest one.

## The pain point as the business sees it

Write it as one sentence a warehouse planner would say out loud. Example: "On a rainy evening at the Jaipur DC, four late trucks all want the same two standard docks and the coordinator spends ninety minutes on the phone."

> Pain point:

## The five whys

Each answer must be a fact you can point to in the data, in the brief, or in a source you cite. If an answer is a guess, mark it [assumption] and plan how you will check it.

| Level | Question | Answer | Evidence (table, query, source) |
|---|---|---|---|
| Why 1 | Why does this happen? | | |
| Why 2 | Why does that happen? | | |
| Why 3 | Why does that happen? | | |
| Why 4 | Why does that happen? | | |
| Why 5 | Why does that happen? | | |

## The root cause in one sentence

> Root cause:

## How you will deal with each why

For each level, decide one of: solve it in your build, mitigate it with a rule, measure it, or leave it out of scope and say why.

| Level | Decision (solve / mitigate / measure / out of scope) | How, in one sentence |
|---|---|---|
| Why 1 | | |
| Why 2 | | |
| Why 3 | | |
| Why 4 | | |
| Why 5 | | |

## Checks before you move on

- The chain reads top to bottom as "because", and bottom to top as "therefore".
- At least two answers cite a table or a query result.
- The root cause is something a system could change, not "drivers are late".



--------------------------------------------------------------------------------------------------------------


# Five Whys worksheet 1: Ambiguous and incomplete driver delay messages

## The pain point as the business sees it

> Pain point: When drivers report delays in informal or incomplete messages, warehouse coordinators must clarify the shipment, revised arrival time, or requested action before they can safely find an alternative dock appointment.

## The five whys

| Level | Question  | Answer  | Evidence (table, query, source) |

| Why 1 | Why does this happen?                                                     | Because some driver messages do not provide enough information to determine the correct next action or update the shipment's ETA.                                     | `driver_messages_labelled.csv`: examples include "Reaching late today" and "Can't make the slot", which provide no revised ETA.                                                                                                                |
| Why 2 | Why do messages lack enough information?                                  | Because drivers communicate in natural language, using vague phrases, approximate times, and sometimes multiple requests in one message.                              | `driver_messages_labelled.csv`: examples include "Late hounga thoda", "Around 2 hours late, maybe more", and messages combining a repair estimate with a delay.                                                                                |
| Why 3 | Why does this create a problem for the warehouse?                         | Because the operational workflow needs specific information, such as the shipment, declared ETA, facility, and appointment requirements, to assess available options. | `driver_exceptions`, `shipments`, `eta_updates`, and `appointments` tables; the SHP1006 / THR001 example traces a delay message through these records.                                                                                         |
| Why 4 | Why can't the workflow reliably handle incomplete messages automatically? | [Assumption] The current workflow does not consistently extract information, identify missing fields, and ask targeted clarification questions before taking action.  | The labelled messages contain different intents and ambiguous examples. The starter kit's agent skeleton includes an understand/clarify workflow, but the current operational workflow's exact automation capabilities have not been verified. |
| Why 5 | Why is that clarification capability important to build?                  | Because acting on an unclear ETA or shipment selection could lead to an incorrect appointment recommendation or operational update.                                   | `appointments`, `eta_updates`, and `driver_exceptions`; the brief requires the database to remain the source of truth and distinguishes shown, held, requested, and confirmed appointments.                                                    |

## The root cause in one sentence

> Root cause: Driver messages arrive as unstructured natural language, while the appointment workflow needs validated, structured shipment and ETA information before it can safely take action.

## How you will deal with each why

| Level | Decision (solve / mitigate / measure / out of scope) | How, in one sentence |  

| Why 1 | Solve                                                | Build an agent that identifies delay reports and extracts the available shipment and ETA information.                                   |
| Why 2 | Mitigate                                             | Handle vague times, multiple intents, and uncertain ETAs by asking drivers targeted clarification questions.                            |
| Why 3 | Solve                                                | Retrieve shipment, facility, and appointment context from the operational database before recommending an action.                       |
| Why 4 | Solve                                                | Implement an understand-and-clarify workflow that checks required information before proceeding.                                        |
| Why 5 | Mitigate                                             | Require database-backed validation and explicit commitment states so an unclear message cannot directly create a confirmed appointment. |


Excellent. Worksheet 1 is complete. Now let's do Worksheet 2: Appointment conflicts and unavailable dock slots.

Copy this into your second Five Whys worksheet.

# Five Whys worksheet 2: Appointment conflicts and unavailable dock slots

## The pain point as the business sees it

> Pain point: When several delayed trucks need alternative appointment times, the warehouse coordinator may find that suitable dock slots are already occupied, blocked, or incompatible with the truck's requirements.

## The five whys

| Level | Question | Answer | Level | Question  | Answer  | Evidence (table, query, source) |

| Why 1 | Why does this happen?                                  | Because a truck's existing appointment may no longer fit its revised arrival time, and alternative slots may not be available.                 | `appointments`, `eta_updates`, and `appointment_slots`; SHP1006 has an ETA of 11:20 while its existing appointment is 10:00–11:00.                              |
| Why 2 | Why might alternative slots not be available?          | Because some slots are occupied by active appointments or marked as blocked.                                                                   | `appointment_slots` and `v_slot_availability`: 72 slots have `OPEN` status, while the availability view reports 58 `AVAILABLE`, 14 `OCCUPIED`, and 7 `BLOCKED`. |
| Why 3 | Why can a slot be blocked or unsuitable?               | Because dock availability depends on operational conditions, including maintenance and dock compatibility requirements.                        | `dock_status_events` and `appointment_slots`: D5 has a maintenance event from 18:00–22:00; SHP1015 requires a reefer-compatible dock.                           |
| Why 4 | Why can't the coordinator simply select any open slot? | Because a slot must be checked against the shipment's requirements and the dock's actual operational availability, not just its `OPEN` status. | `v_slot_availability`, `dock_status_events`, `shipments`, and the database guide.                                                                               |
| Why 5 | Why is a reliable feasibility check necessary?         | Because offering an occupied, blocked, or incompatible slot can create an appointment conflict and disrupt warehouse operations.               | The brief's operational requirements and the database's appointment and dock-status records.                                                                    |

## The root cause in one sentence

> Root cause: Appointment selection requires a reliable, database-backed feasibility check that considers slot occupancy, dock compatibility, maintenance, and the truck's arrival and unloading requirements.

## How you will deal with each why

| Level | Decision (solve / mitigate / measure / out of scope) | How, in one sentence |

| Why 1 | Solve                                                | Retrieve the current appointment and revised ETA before searching for alternatives.                                           |
| Why 2 | Solve                                                | Query actual slot availability rather than relying only on the slot's `OPEN` status.                                          |
| Why 3 | Solve                                                | Check dock compatibility and operational blocks before presenting a candidate slot.                                           |
| Why 4 | Solve                                                | Use database-backed rules and the ML unloading-duration estimate to check whether a candidate slot can accommodate the truck. |
| Why 5 | Mitigate                                             | Use transactional slot holds and explicit appointment states to prevent conflicting commitments.                              |

One important distinction: `OPEN` does not necessarily mean `AVAILABLE`. The availability view is the better source for determining whether a slot can actually be offered.



# Five Whys worksheet 3: Inaccurate unloading-duration estimates

## The pain point as the business sees it

> Pain point: When coordinators estimate how long a truck will occupy a dock, inaccurate unloading times can cause unsuitable appointment windows and make dock scheduling less reliable.

## The five whys

| Level | Question | Answer | Evidence (table, query, source)  

| Why 1 | Why does this happen?                                  | Because unloading duration varies considerably between trucks and dock types.                                                                                | `dock_visit_history.csv`: STANDARD median 31 minutes, HEAVY median 76 minutes, REEFER median 39 minutes.                                       |
| Why 2 | Why does unloading duration vary?                      | Because different loads have different characteristics, including pallet count, weight, dock type, and temperature-control requirements.                     | `dock_visit_history.csv` and `skyways_data_dictionary.csv`.                                                                                    |
| Why 3 | Why can a simple fixed estimate be unreliable?         | Because the historical unloading times show substantial variation, even within the same dock type.                                                           | `dock_visit_history.csv`: STANDARD unload duration ranges from 20 to 392 minutes; HEAVY from 51 to 297 minutes; REEFER from 20 to 384 minutes. |
| Why 4 | Why might coordinators need a better estimate?         | Because underestimating unloading duration can make a proposed slot too short, while overestimating it can unnecessarily restrict scheduling options.        | [Assumption] This operational effect is plausible, but its actual frequency and cost have not yet been measured in the supplied data.          |
| Why 5 | Why is a data-driven estimate a practical improvement? | Because historical dock visits can be used to train and evaluate a model that estimates unloading duration from available shipment and operational features. | `dock_visit_history.csv`, `04_build/ml/feature_spec.md`, and the capstone brief.                                                               |

## The root cause in one sentence

> Root cause: Unloading duration varies with load and operational characteristics, so a single fixed estimate cannot adequately represent the time different trucks may need at a dock.

## How you will deal with each why

| Level | Decision (solve / mitigate / measure / out of scope) | How, in one sentence  |

| Why 1 | Solve                                                | Build an ML model that predicts unloading duration for an incoming shipment.                                          |
| Why 2 | Solve                                                | Use relevant shipment and operational features such as pallet count, load weight, and dock type.                      |
| Why 3 | Solve                                                | Compare a machine-learning model against a median-by-dock-type baseline using a chronological train/test split.       |
| Why 4 | Measure                                              | Evaluate prediction errors and investigate how often estimates underestimate actual unloading duration.               |
| Why 5 | Mitigate                                             | Use a conservative p90 unloading-duration estimate when checking whether a candidate appointment slot is long enough. |

## Checks before you move on

- The chain connects the problem to a system-level root cause.
- Multiple answers cite the historical dataset or project files.
- The root cause is something the system can improve.
- Unsupported operational impacts are marked as assumptions.

Important: The large maximum unloading times may include unusual cases. Do not remove them without documenting and investigating the outliers. Also, exclude `NO_SHOW` records from unloading-duration model training, as required by the project brief.

