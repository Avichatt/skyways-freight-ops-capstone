import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Professional Wireframe / C4 Architecture Canvas
# Sized with generous padding so every element and label has ample breathing room
fig, ax = plt.subplots(figsize=(19, 14.5), dpi=160)
ax.set_xlim(0, 19)
ax.set_ylim(0, 14.5)
ax.axis("off")

# Architectural Theme Colors
bg_canvas = "#0a0e17"
fig.patch.set_facecolor(bg_canvas)
ax.set_facecolor(bg_canvas)

panel_bg = "#111827"
box_bg_inner = "#0b1220"
border_wire = "#27354f"

c_blue = "#38bdf8"
c_teal = "#2dd4bf"
c_purple = "#a855f7"
c_amber = "#f59e0b"
c_green = "#10b981"

txt_main = "#f8fafc"
txt_sub = "#94a3b8"

# ===========================================================================
# 1. MAIN TITLE
# ===========================================================================
ax.text(9.5, 13.9, "SkyWays Smart Dock Coordination System", 
        fontsize=18, fontweight="bold", color=txt_main, ha="center")
ax.text(9.5, 13.55, "Hybrid Simple Architecture: Tool-Calling Agentic AI  +  Predictive ML Sizing  +  Transactional SQLite System of Record", 
        fontsize=10.5, color=txt_sub, ha="center")

ax.plot([0.8, 18.2], [13.25, 13.25], color="#1e293b", linewidth=1.5)

# ===========================================================================
# 2. TOP SECTION: HIGH-LEVEL 4-STEP WORKFLOW (Beginner Friendly)
# ===========================================================================
ax.text(0.8, 12.85, "PART 1: HIGH-LEVEL OPERATIONAL FLOW (HOW IT WORKS)", 
        fontsize=12, fontweight="bold", color=c_amber, ha="left")
ax.text(0.8, 12.55, "A driver delayed by traffic sends a free-text message. The system safely finds, sizes, and reserves a dock door without double-booking.",
        fontsize=9, color=txt_sub, ha="left")

top_y = 9.0
top_h = 3.3
card_w = 4.0
card_gap = 0.35
cards_x = [0.8, 0.8 + card_w + card_gap, 0.8 + (card_w + card_gap)*2, 0.8 + (card_w + card_gap)*3]

def draw_top_card(x, step_num, title, subtitle, bullets, rule_text, accent_color):
    # Card outer container
    rect = patches.FancyBboxPatch((x, top_y), card_w, top_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                  facecolor=panel_bg, edgecolor=accent_color, linewidth=1.5)
    ax.add_patch(rect)
    
    # Step Badge
    badge = patches.Circle((x + 0.42, top_y + top_h - 0.42), 0.22, facecolor=accent_color, edgecolor="none")
    ax.add_patch(badge)
    ax.text(x + 0.42, top_y + top_h - 0.42, str(step_num), fontsize=10, fontweight="bold", color="#090d16", ha="center", va="center")
    
    # Header
    ax.text(x + 0.78, top_y + top_h - 0.32, title, fontsize=10.5, fontweight="bold", color=txt_main, va="center")
    ax.text(x + 0.78, top_y + top_h - 0.55, subtitle, fontsize=8, color=accent_color, va="center")
    
    # Inner Content Box
    inner_h = 1.65
    inner_y = top_y + 0.85
    inner_rect = patches.FancyBboxPatch((x + 0.2, inner_y), card_w - 0.4, inner_h, boxstyle="round,pad=0.05,rounding_size=0.08",
                                       facecolor=box_bg_inner, edgecolor=border_wire, linewidth=1)
    ax.add_patch(inner_rect)
    
    # Text inside inner box
    line_y = inner_y + inner_h - 0.30
    for b in bullets:
        ax.text(x + 0.35, line_y, b, fontsize=8, color=txt_main, va="center")
        line_y -= 0.28
        
    # Bottom Rule Callout Strip
    rule_rect = patches.FancyBboxPatch((x + 0.2, top_y + 0.18), card_w - 0.4, 0.52, boxstyle="round,pad=0.04,rounding_size=0.06",
                                       facecolor="#1e293b", edgecolor=accent_color, linewidth=0.8)
    ax.add_patch(rule_rect)
    ax.text(x + card_w/2, top_y + 0.44, rule_text, fontsize=7.5, fontweight="bold", color=accent_color, ha="center", va="center")

# Step 1
draw_top_card(
    cards_x[0], 1, "Driver Sends Delay", "Cab Message (WhatsApp/SMS)",
    [
        "Driver: 'Traffic after Shahpura.",
        "Reaching around 11:20. Slot after 12?'",
        "",
        "-> Agent extracts: ETA 11:20",
        "-> Constraint: Not before 12:00"
    ],
    "RULE: Agent understands; never books.",
    c_blue
)

# Step 2
draw_top_card(
    cards_x[1], 2, "ML Sizes Unload Time", "Prevents Overrun Cascades",
    [
        "Load: 17,000 kg, 28 pallets (Standard)",
        "Historical visits analyzed by Model.",
        "",
        "-> Point Estimate: 45 min",
        "-> Conservative p90 Band: 78 min",
        "-> Rejects any slot < 78 mins"
    ],
    "RULE: p90 duration prevents yard overruns.",
    c_purple
)

# Step 3
draw_top_card(
    cards_x[2], 3, "Atomic 10-Min Hold", "Concurrency Protection in SQLite",
    [
        "Driver replies: 'Take the first one.'",
        "Agent executes BEGIN IMMEDIATE.",
        "",
        "-> Slot status set to HELD (10 min)",
        "-> Partial Unique Index blocks",
        "    any other driver from this slot."
    ],
    "RULE: 0 double-bookings under race conditions.",
    c_amber
)

# Step 4
draw_top_card(
    cards_x[3], 4, "Warehouse Confirms", "Human-in-the-Loop Authority",
    [
        "System sends confirmation request",
        "to Warehouse Operations team.",
        "",
        "-> Coordinator approves the request",
        "-> Status transitions to CONFIRMED",
        "-> Driver receives verified gate pass"
    ],
    "RULE: Autonomous hold; human commits.",
    c_green
)

# Connecting Arrows between Steps
for i in range(3):
    ax.annotate("", xy=(cards_x[i+1] - 0.08, top_y + top_h/2), 
                xytext=(cards_x[i] + card_w + 0.08, top_y + top_h/2),
                arrowprops=dict(arrowstyle="-|>", color=c_teal, lw=2.2, mutation_scale=16))

# ===========================================================================
# 3. BOTTOM SECTION: C4 CONTAINERS & THE THREE RINGS OF DECISION
# ===========================================================================
ax.plot([0.8, 18.2], [8.55, 8.55], color="#1e293b", linewidth=1.5)

ax.text(0.8, 8.15, "PART 2: SYSTEM ARCHITECTURE & THE THREE RINGS OF DECISION", 
        fontsize=12, fontweight="bold", color=c_blue, ha="left")
ax.text(0.8, 7.85, "Strict architectural boundaries prevent hallucinations: The LLM decides what to say, tools decide what is true, SQLite decides what is committed.",
        fontsize=9, color=txt_sub, ha="left")

bot_y = 0.5
bot_h = 7.0

# Column 1: Touchpoint
c1_x = 0.8
c1_w = 3.2
rect1 = patches.FancyBboxPatch((c1_x, bot_y), c1_w, bot_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                              facecolor=panel_bg, edgecolor=c_amber, linewidth=1.5)
ax.add_patch(rect1)
ax.text(c1_x + c1_w/2, bot_y + bot_h - 0.35, "CLIENT & TOUCHPOINT", fontsize=8.5, fontweight="bold", color=c_amber, ha="center")
ax.text(c1_x + c1_w/2, bot_y + bot_h - 0.70, "Driver Mobile Interface", fontsize=11, fontweight="bold", color=txt_main, ha="center")
ax.plot([c1_x + 0.25, c1_x + c1_w - 0.25], [bot_y + bot_h - 0.95, bot_y + bot_h - 0.95], color=border_wire, linewidth=1)

c1_items = [
    "• Chat Channel (WhatsApp / SMS)",
    "• Drivers report route delays & ETAs",
    "• States specific time constraints",
    "• Selects offered dock options",
    "",
    "Core Guarantee:",
    "Driver always receives unambiguous",
    "commitment status in the first line:",
    "NONE, SHOWN, HELD, REQUESTED,",
    "CONFIRMED, or ESCALATED.",
    "",
    "Never sees raw database errors",
    "or unhandled system exceptions."
]
c1_cur_y = bot_y + bot_h - 1.35
for item in c1_items:
    color = c_amber if "Guarantee" in item else txt_main
    fontweight = "bold" if "Guarantee" in item else "normal"
    ax.text(c1_x + 0.25, c1_cur_y, item, fontsize=8.5, color=color, fontweight=fontweight, va="center")
    c1_cur_y -= 0.35


# Column 2: Ring 1 - LangGraph Agent & LLM
c2_x = 4.45
c2_w = 4.3
rect2 = patches.FancyBboxPatch((c2_x, bot_y), c2_w, bot_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                              facecolor=panel_bg, edgecolor=c_blue, linewidth=1.5)
ax.add_patch(rect2)
ax.text(c2_x + c2_w/2, bot_y + bot_h - 0.35, "RING 1: DECIDES WHAT TO SAY", fontsize=8.5, fontweight="bold", color=c_blue, ha="center")
ax.text(c2_x + c2_w/2, bot_y + bot_h - 0.70, "LangGraph Agent (StateGraph)", fontsize=11, fontweight="bold", color=txt_main, ha="center")
ax.plot([c2_x + 0.25, c2_x + c2_w - 0.25], [bot_y + bot_h - 0.95, bot_y + bot_h - 0.95], color=border_wire, linewidth=1)

c2_items = [
    "Workflow Nodes (src/agent/agent_skeleton.py):",
    "1. understand: LLM extracts intent & fields",
    "2. clarify: 1 targeted question (<= 20 words)",
    "3. options: queries feasible dock doors",
    "4. hold: places atomic 10-min slot reservation",
    "5. request: dispatches warehouse confirmation",
    "6. escalate: hands off to human operations",
    "7. reply: composes concise cab response",
    "",
    "Conversation State (state.py):",
    "• Thread ID, Driver ID, Shipment ID",
    "• Commitment Status & Tools Called Log",
    "",
    "STRICT GUARDRAIL:",
    "External LLM never writes SQL, never",
    "computes availability, & never says CONFIRMED."
]
c2_cur_y = bot_y + bot_h - 1.35
for item in c2_items:
    color = c_blue if "GUARDRAIL" in item or "Nodes" in item or "State" in item else txt_main
    fontweight = "bold" if "GUARDRAIL" in item or "Nodes" in item else "normal"
    ax.text(c2_x + 0.25, c2_cur_y, item, fontsize=8.3, color=color, fontweight=fontweight, va="center")
    c2_cur_y -= 0.34


# Column 3: Ring 2 - Typed Tools & ML Predictor
c3_x = 9.2
c3_w = 4.3

# Top Box in Col 3: Typed Tools Module
t_box_h = 3.9
rect3_top = patches.FancyBboxPatch((c3_x, bot_y + bot_h - t_box_h), c3_w, t_box_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                   facecolor=panel_bg, edgecolor=c_teal, linewidth=1.5)
ax.add_patch(rect3_top)
ax.text(c3_x + c3_w/2, bot_y + bot_h - 0.35, "RING 2: DECIDES WHAT IS TRUE", fontsize=8.5, fontweight="bold", color=c_teal, ha="center")
ax.text(c3_x + c3_w/2, bot_y + bot_h - 0.70, "Typed Tools Module (src/tools.py)", fontsize=11, fontweight="bold", color=txt_main, ha="center")
ax.plot([c3_x + 0.25, c3_x + c3_w - 0.25], [bot_y + bot_h - 0.95, bot_y + bot_h - 0.95], color=border_wire, linewidth=1)

c3_t_items = [
    "• get_driver_context() & get_latest_eta()",
    "• find_feasible_slots() enforces 6 checks:",
    "   1. Start >= driver's revised ETA",
    "   2. Dock type compatible (Standard/Reefer)",
    "   3. Status is AVAILABLE (not OCCUPIED)",
    "   4. Unload duration fits using ML p90",
    "   5. Before 21:00 facility curfew limit",
    "   6. Unload finishes before driver's leave time",
    "• hold_slot() runs atomic BEGIN IMMEDIATE",
    "• release_expired_holds() cancels stale holds"
]
c3_t_cur_y = bot_y + bot_h - 1.30
for item in c3_t_items:
    ax.text(c3_x + 0.25, c3_t_cur_y, item, fontsize=8.2, color=txt_main, va="center")
    c3_t_cur_y -= 0.28

# Bottom Box in Col 3: ML Duration Predictor
b_box_h = 2.6
rect3_bot = patches.FancyBboxPatch((c3_x, bot_y), c3_w, b_box_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                                   facecolor=panel_bg, edgecolor=c_purple, linewidth=1.5)
ax.add_patch(rect3_bot)
ax.text(c3_x + c3_w/2, bot_y + b_box_h - 0.32, "RING 2: STATISTICAL PREDICTOR", fontsize=8.5, fontweight="bold", color=c_purple, ha="center")
ax.text(c3_x + c3_w/2, bot_y + b_box_h - 0.65, "Unload Regressor & Late Classifier", fontsize=10.5, fontweight="bold", color=txt_main, ha="center")
ax.plot([c3_x + 0.25, c3_x + c3_w - 0.25], [bot_y + b_box_h - 0.88, bot_y + b_box_h - 0.88], color=border_wire, linewidth=1)

c3_b_items = [
    "• Random Forest Regressor: MAE 8.08 min (vs 13.90 baseline)",
    "• Features: Weight, pallets, dock type, carrier, hour",
    "• Uses conservative p90 duration for slot sizing",
    "• 3-Tier Fallback: HTTP Service -> In-Process -> DB Default",
    "• Late Arrival Classifier (ROC AUC: 0.746)"
]
c3_b_cur_y = bot_y + b_box_h - 1.15
for item in c3_b_items:
    ax.text(c3_x + 0.25, c3_b_cur_y, item, fontsize=8.1, color=txt_main, va="center")
    c3_b_cur_y -= 0.27


# Column 4: Ring 3 - SQLite System of Record
c4_x = 13.95
c4_w = 4.25
rect4 = patches.FancyBboxPatch((c4_x, bot_y), c4_w, bot_h, boxstyle="round,pad=0.08,rounding_size=0.12",
                              facecolor=panel_bg, edgecolor=c_green, linewidth=1.5)
ax.add_patch(rect4)
ax.text(c4_x + c4_w/2, bot_y + bot_h - 0.35, "RING 3: DECIDES WHAT IS COMMITTED", fontsize=8.5, fontweight="bold", color=c_green, ha="center")
ax.text(c4_x + c4_w/2, bot_y + bot_h - 0.70, "SQLite Database (System of Record)", fontsize=11, fontweight="bold", color=txt_main, ha="center")
ax.plot([c4_x + 0.25, c4_x + c4_w - 0.25], [bot_y + bot_h - 0.95, bot_y + bot_h - 0.95], color=border_wire, linewidth=1)

c4_items = [
    "Operational Tables:",
    "• shipments & appointment_slots",
    "• appointments & facility_rules",
    "• operational_messages & chat_threads",
    "",
    "Dynamic Views:",
    "• v_slot_availability (real-time free slots)",
    "• v_latest_eta (most recent driver ETA)",
    "",
    "CRITICAL CONCURRENCY ARBITER:",
    "Unique Partial Index:",
    "ux_active_appointment_per_slot",
    "ON appointments(slot_id)",
    "WHERE appointment_status IN",
    "('PENDING_CONFIRMATION', 'CONFIRMED',",
    "'IN_PROGRESS')",
    "",
    "Guarantees that competing writes raise",
    "IntegrityError and are safely rejected."
]
c4_cur_y = bot_y + bot_h - 1.35
for item in c4_items:
    color = c_green if "ARBITER" in item or "Tables" in item or "Views" in item else txt_main
    fontweight = "bold" if "ARBITER" in item or "Tables" in item or "Views" in item else "normal"
    ax.text(c4_x + 0.25, c4_cur_y, item, fontsize=8.2, color=color, fontweight=fontweight, va="center")
    c4_cur_y -= 0.30


# Clean Non-Colliding Connection Arrows
# Driver <-> Agent
ax.annotate("", xy=(c2_x - 0.05, bot_y + 6.0), xytext=(c1_x + c1_w + 0.05, bot_y + 6.0),
            arrowprops=dict(arrowstyle="<->", color=c_amber, lw=1.6, ls="--"))
ax.text((c1_x + c1_w + c2_x)/2, bot_y + 6.22, "Chat / Status", fontsize=7.5, fontweight="bold", color=c_amber, ha="center")

# Agent <-> Typed Tools
ax.annotate("", xy=(c3_x - 0.05, bot_y + 6.0), xytext=(c2_x + c2_w + 0.05, bot_y + 6.0),
            arrowprops=dict(arrowstyle="<->", color=c_blue, lw=1.6, ls="--"))
ax.text((c2_x + c2_w + c3_x)/2, bot_y + 6.22, "Typed Tools Call", fontsize=7.5, fontweight="bold", color=c_blue, ha="center")

# Typed Tools <-> SQLite
ax.annotate("", xy=(c4_x - 0.05, bot_y + 6.0), xytext=(c3_x + c3_w + 0.05, bot_y + 6.0),
            arrowprops=dict(arrowstyle="<->", color=c_green, lw=1.6, ls="--"))
ax.text((c3_x + c3_w + c4_x)/2, bot_y + 6.22, "Atomic SQL", fontsize=7.5, fontweight="bold", color=c_green, ha="center")

# Typed Tools <-> ML Predictor (Vertical)
gap_mid_y = (bot_y + b_box_h + bot_y + bot_h - t_box_h) / 2
ax.annotate("", xy=(c3_x + c3_w/2, bot_y + b_box_h + 0.08), 
            xytext=(c3_x + c3_w/2, bot_y + bot_h - t_box_h - 0.08),
            arrowprops=dict(arrowstyle="<->", color=c_purple, lw=1.6, ls="--"))
ax.text(c3_x + c3_w/2 + 1.25, gap_mid_y, "Query p90 (<=300ms SLA)", fontsize=7.5, fontweight="bold", color=c_purple, ha="center", va="center")

plt.tight_layout()
plt.savefig("docs/architecture.png", dpi=160, facecolor=fig.get_facecolor(), edgecolor="none")
plt.close()
print("Saved clean wireframe architecture diagram to docs/architecture.png successfully.")
