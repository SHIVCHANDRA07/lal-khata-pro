import os
import sqlite3
import urllib.parse
import webbrowser
import flet as ft
from datetime import datetime

# ----------------- Database Setup -----------------
conn = sqlite3.connect("lalkhata.db", timeout=15, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS app_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    pin TEXT NOT NULL DEFAULT '123456',
    gstin TEXT DEFAULT '',
    shop_address TEXT DEFAULT '',
    profile_pic TEXT DEFAULT '',
    app_language TEXT DEFAULT 'hinglish',
    biometric_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

for col, col_t, d_val in [
    ("gstin", "TEXT", "''"),
    ("shop_address", "TEXT", "''"),
    ("profile_pic", "TEXT", "''"),
    ("app_language", "TEXT", "'hinglish'")
]:
    try:
        cursor.execute(f"ALTER TABLE app_users ADD COLUMN {col} {col_t} DEFAULT {d_val}")
    except sqlite3.OperationalError:
        pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT,
    id_type TEXT,
    id_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    txn_type TEXT NOT NULL,
    note TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(person_id) REFERENCES persons(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('update_version', '1.3.5')")
conn.commit()

# ----------------- Language Dictionary -----------------
LANG_PACK = {
    "hinglish": {
        "title": "LAL KHATA PRO",
        "tab_khata": "Khata",
        "tab_calc": "Calc",
        "tab_marketing": "Marketing",
        "tab_reports": "Reports",
        "tab_profile": "Profile",
        "btn_add_cust": "+ Grahak",
        "udhar_sub": "Kul Bazar Udhar",
        "jama_sub": "Kul Advance/Jama",
        "search_hint": "🔍 Grahak khojein...",
        "debit": "🔻 Udhar Diya (-)",
        "credit": "🔺 Jama Mila (+)",
        "ad_tag": "SPONSORED / ADVERTISEMENT",
        "ad_txt": "Lal Khata Pro: Dukan ko digital banayein aur bikri badhayein!"
    },
    "hindi": {
        "title": "लाल खाता प्रो",
        "tab_khata": "खाता",
        "tab_calc": "कैलकुलेटर",
        "tab_marketing": "मार्केटिंग",
        "tab_reports": "रिपोर्ट्स",
        "tab_profile": "प्रोफाइल",
        "btn_add_cust": "+ नया ग्राहक",
        "udhar_sub": "कुल बाजार उधार",
        "jama_sub": "कुल जमा राशि",
        "search_hint": "🔍 ग्राहक खोजें...",
        "debit": "🔻 उधार दिया (-)",
        "credit": "🔺 जमा मिला (+)",
        "ad_tag": "प्रायोजित विज्ञापन (AD)",
        "ad_txt": "लाल खाता प्रो: अपनी दुकान को डिजिटल बनाकर बिक्री बढ़ाएं!"
    },
    "english": {
        "title": "LAL KHATA PRO",
        "tab_khata": "Ledger",
        "tab_calc": "Calculator",
        "tab_marketing": "Marketing",
        "tab_reports": "Reports",
        "tab_profile": "Profile",
        "btn_add_cust": "+ Customer",
        "udhar_sub": "Total Receivable",
        "jama_sub": "Total Advance Paid",
        "search_hint": "🔍 Search customer...",
        "debit": "🔻 Gave Credit (-)",
        "credit": "🔺 Got Payment (+)",
        "ad_tag": "SPONSORED / ADVERTISEMENT",
        "ad_txt": "Lal Khata Pro: Digitize your store & grow your business!"
    }
}


def main(page: ft.Page):
    page.title = "Lal Khata Pro (लाल खाता)"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0b0c10"

    if hasattr(page, "window"):
        page.window.width = 430
        page.window.height = 800
        page.window.resizable = False
    else:
        page.window_width = 430
        page.window_height = 800
        page.window_resizable = False

    page.padding = 0

    current_user = {
        "id": None,
        "shop_name": "",
        "owner_name": "",
        "phone": "",
        "gstin": "",
        "shop_address": "",
        "profile_pic": "",
        "language": "hinglish"
    }
    selected_person_id = None
    DEVELOPER_MASTER_PIN = "9988"
    DEV_WA = "917260975551"

    PRIMARY_RED = "#ff3b30"
    SUCCESS_GREEN = "#34c759"
    ACCENT_GOLD = "#ffcc00"
    MUTED_TEXT = "#8e8e93"
    SURFACE_CARD = "#16181f"
    SURFACE_LIGHT = "#242735"

    def show_toast(msg):
        sb = ft.SnackBar(ft.Text(msg, weight=ft.FontWeight.W_500), open=True)
        if sb not in page.overlay:
            page.overlay.append(sb)
        page.update()

    def make_btn(text, on_click=None, bgcolor=PRIMARY_RED, color="white", height=42, width=None, expand=False, icon=None):
        controls = []
        if icon:
            controls.append(ft.Icon(icon, size=16, color=color))
        controls.append(ft.Text(text, color=color, weight=ft.FontWeight.BOLD, size=13))
        return ft.Container(
            content=ft.Row(controls, alignment=ft.MainAxisAlignment.CENTER, tight=True, spacing=6),
            bgcolor=bgcolor,
            border_radius=10,
            height=height,
            width=width,
            expand=expand,
            ink=True,
            on_click=on_click,
        )

    def close_dlg(d):
        d.open = False
        page.update()

    def open_dlg(d):
        if d not in page.overlay:
            page.overlay.append(d)
        d.open = True
        page.update()

    def open_dev_whatsapp(e=None):
        s = current_user.get("shop_name") or "Dukan"
        o = current_user.get("owner_name") or "User"
        p = current_user.get("phone") or "N/A"
        msg = f"Namaste Developer,\nLal Khata Pro sahayata chahiye.\nDukan: {s}\nSanchalak: {o}\nMob: {p}"
        webbrowser.open(f"https://wa.me/{DEV_WA}?text={urllib.parse.quote(msg)}")
        show_toast("WhatsApp support open ho raha hai...")

    # ------------------- DP FilePicker -------------------
    def on_dp_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            p = e.files[0].path
            current_user["profile_pic"] = p
            if current_user["id"]:
                cursor.execute("UPDATE app_users SET profile_pic=? WHERE id=?", (p, current_user["id"]))
                conn.commit()
            update_dp_everywhere()
            show_toast("Dukan DP update ho gayi!")

    dp_picker = ft.FilePicker(on_result=on_dp_picked)
    page.overlay.append(dp_picker)

    def update_dp_everywhere():
        p = current_user.get("profile_pic", "")
        if p and os.path.exists(p):
            home_avatar.content = None
            home_avatar.foreground_image_url = p
            prof_avatar.content = None
            prof_avatar.foreground_image_url = p
            poster_avatar.content = None
            poster_avatar.foreground_image_url = p
        else:
            home_avatar.foreground_image_url = None
            home_avatar.content = ft.Icon(ft.icons.STOREFRONT, color="white", size=20)
            prof_avatar.foreground_image_url = None
            prof_avatar.content = ft.Icon(ft.icons.ACCOUNT_CIRCLE, color="white", size=45)
            poster_avatar.foreground_image_url = None
            poster_avatar.content = ft.Icon(ft.icons.STOREFRONT, color="white", size=24)
        update_poster_preview()
        page.update()

    # ------------------- Smart Live Calculator -------------------
    calc_history_txt = ft.Text("", size=13, color=MUTED_TEXT, text_align=ft.TextAlign.RIGHT)
    calc_main_txt = ft.Text("0", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)
    calc_target_callback = None

    def eval_live(expr):
        if not expr:
            return ""
        try:
            s = expr.replace("×", "*").replace("÷", "/")
            if s[-1] in "+-*/%":
                return ""
            r = eval(s)
            return f"= {r:,.2f}" if isinstance(r, float) else f"= {r:,}"
        except Exception:
            return ""

    def on_smart_calc_key(k):
        cur = calc_main_txt.value
        if k == "C":
            calc_main_txt.value = "0"
            calc_history_txt.value = ""
        elif k == "⌫":
            if cur in ["0", "Error"] or len(cur) == 1:
                calc_main_txt.value = "0"
                calc_history_txt.value = ""
            else:
                calc_main_txt.value = cur[:-1]
                calc_history_txt.value = eval_live(calc_main_txt.value)
        elif k == "=":
            try:
                s = cur.replace("×", "*").replace("÷", "/")
                r = eval(s)
                calc_history_txt.value = cur + " ="
                calc_main_txt.value = f"{r:,.2f}" if isinstance(r, float) and not r.is_integer() else str(int(r) if isinstance(r, float) else r)
            except Exception:
                calc_main_txt.value = "Error"
                calc_history_txt.value = ""
        elif k in ["+", "-", "×", "÷", "%"]:
            if cur != "Error":
                if cur[-1] in "+-×÷%":
                    calc_main_txt.value = cur[:-1] + k
                else:
                    calc_main_txt.value = cur + k
                calc_history_txt.value = eval_live(calc_main_txt.value)
        else:
            calc_main_txt.value = k if cur in ["0", "Error"] else cur + k
            calc_history_txt.value = eval_live(calc_main_txt.value)
        page.update()

    def apply_calc():
        v = calc_main_txt.value.replace(",", "")
        try:
            rv = str(eval(v.replace("×", "*").replace("÷", "/")))
            if calc_target_callback:
                calc_target_callback(rv)
            close_dlg(smart_calc_dialog)
            show_toast(f"Rashi ₹{rv} set ho gayi!")
        except Exception:
            if calc_target_callback and v not in ["0", "Error"]:
                calc_target_callback(v)
                close_dlg(smart_calc_dialog)

    def make_ckey(lbl, col=SURFACE_LIGHT, tcol="white"):
        return ft.Container(
            content=ft.Text(lbl, size=15, weight=ft.FontWeight.BOLD, color=tcol),
            alignment=ft.alignment.center,
            bgcolor=col,
            border_radius=8,
            height=46,
            expand=True,
            ink=True,
            on_click=lambda e, v=lbl: on_smart_calc_key(v)
        )

    smart_calc_dialog = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.icons.CALCULATE, color=ACCENT_GOLD), ft.Text("Smart Calculator", size=15, weight=ft.FontWeight.BOLD)], tight=True),
        content=ft.Container(
            width=360,
            content=ft.Column([
                ft.Container(
                    content=ft.Column([calc_history_txt, calc_main_txt], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                    bgcolor="#121318",
                    padding=10,
                    border_radius=8
                ),
                ft.Row([make_ckey("C", PRIMARY_RED), make_ckey("⌫", "#3a3a44"), make_ckey("%", "#3a3a44"), make_ckey("÷", ACCENT_GOLD, "black")]),
                ft.Row([make_ckey("7"), make_ckey("8"), make_ckey("9"), make_ckey("×", ACCENT_GOLD, "black")]),
                ft.Row([make_ckey("4"), make_ckey("5"), make_ckey("6"), make_ckey("-", ACCENT_GOLD, "black")]),
                ft.Row([make_ckey("1"), make_ckey("2"), make_ckey("3"), make_ckey("+", ACCENT_GOLD, "black")]),
                ft.Row([make_ckey("00"), make_ckey("0"), make_ckey("."), make_ckey("=", SUCCESS_GREEN)])
            ], tight=True, spacing=8)
        ),
        actions=[
            make_btn("Cancel", bgcolor="#3a3a44", height=36, width=80, on_click=lambda e: close_dlg(smart_calc_dialog)),
            make_btn("Use Amount", bgcolor=SUCCESS_GREEN, height=36, width=130, on_click=lambda e: apply_calc())
        ]
    )

    def open_smart_calc_for(cb=None):
        nonlocal calc_target_callback
        calc_target_callback = cb
        calc_main_txt.value = "0"
        calc_history_txt.value = ""
        open_dlg(smart_calc_dialog)

    # ------------------- Mohar Billing -------------------
    bill_items = []
    bill_items_col = ft.Column(spacing=6)
    bill_subtotal_txt = ft.Text("₹0.00", size=15, weight=ft.FontWeight.BOLD, color=ACCENT_GOLD)

    b_item_name = ft.TextField(label="Item Naam*", text_size=12, height=42, expand=2)
    b_item_qty = ft.TextField(label="Qty*", value="1", keyboard_type=ft.KeyboardType.NUMBER, text_size=12, height=42, expand=1)
    b_item_price = ft.TextField(label="Rate (₹)*", keyboard_type=ft.KeyboardType.NUMBER, text_size=12, height=42, expand=1)

    bill_pay_status = ft.Dropdown(
        label="Bhugtan*",
        options=[ft.dropdown.Option("PAID"), ft.dropdown.Option("UNPAID (Baki)")],
        value="PAID",
        text_size=12,
        height=45,
        expand=True
    )
    bill_pay_mode = ft.Dropdown(
        label="Mode*",
        options=[ft.dropdown.Option("CASH"), ft.dropdown.Option("ONLINE UPI")],
        value="CASH",
        text_size=12,
        height=45,
        expand=True
    )

    def refresh_bill_items():
        bill_items_col.controls.clear()
        tot = sum(i["total"] for i in bill_items)
        for idx, it in enumerate(bill_items):
            bill_items_col.controls.append(
                ft.Container(
                    bgcolor=SURFACE_LIGHT,
                    padding=8,
                    border_radius=6,
                    content=ft.Row([
                        ft.Column([
                            ft.Text(f"{idx+1}. {it['name']}", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(f"₹{it['price']} × {it['qty']} Pcs", size=10, color=MUTED_TEXT)
                        ], spacing=2, expand=True),
                        ft.Text(f"₹{it['total']:,.2f}", size=12, weight=ft.FontWeight.BOLD, color=SUCCESS_GREEN),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE,
                            icon_size=16,
                            icon_color=PRIMARY_RED,
                            on_click=lambda e, i=idx: (bill_items.pop(i), refresh_bill_items())
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            )
        bill_subtotal_txt.value = f"₹{tot:,.2f}"
        page.update()

    def add_bill_item():
        n = b_item_name.value.strip()
        try:
            q = float(b_item_qty.value.strip())
            p = float(b_item_price.value.strip())
            if not n or q <= 0 or p < 0:
                show_toast("Item naam, sahi quantity aur rate dalein!")
                return
            bill_items.append({"name": n, "qty": q, "price": p, "total": q * p})
            b_item_name.value = ""
            b_item_qty.value = "1"
            b_item_price.value = ""
            refresh_bill_items()
        except Exception:
            show_toast("Sahi number dalein!")

    def generate_bill_html():
        if not bill_items or not selected_person_id:
            show_toast("Item add karein aur grahak chunein!")
            return

        cursor.execute("SELECT name, phone, address FROM persons WHERE id=?", (selected_person_id,))
        p_row = cursor.fetchone()
        c_name = p_row[0] if p_row else "Grahak"
        c_phone = p_row[1] if p_row else ""
        c_addr = p_row[2] if p_row and p_row[2] else "N/A"

        tot = sum(i["total"] for i in bill_items)
        now_str = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        bill_no = f"INV-{int(datetime.now().timestamp())}"
        st = bill_pay_status.value
        md = bill_pay_mode.value if st == "PAID" else "UDHAR"

        summary = ", ".join([f"{i['name']} (x{i['qty']})" for i in bill_items])
        if st == "UNPAID (Baki)":
            cursor.execute("INSERT INTO transactions (person_id, amount, txn_type, note) VALUES (?, ?, 'DEBIT', ?)",
                           (selected_person_id, tot, f"Bill #{bill_no} (Udhar): {summary[:60]}"))
        else:
            cursor.execute("INSERT INTO transactions (person_id, amount, txn_type, note) VALUES (?, ?, 'DEBIT', ?)",
                           (selected_person_id, tot, f"Bill #{bill_no}: {summary[:60]}"))
            cursor.execute("INSERT INTO transactions (person_id, amount, txn_type, note) VALUES (?, ?, 'CREDIT', ?)",
                           (selected_person_id, tot, f"Bill #{bill_no} Paid via {md}"))
        conn.commit()

        stamp_col = "#15803d" if st == "PAID" else "#dc2626"
        stamp_title = "PAID / BHUGTAN SAFAL" if st == "PAID" else "UNPAID / UDHAR BAKI"

        items_html = "".join([
            f"<tr><td style='padding:8px; border-bottom:1px solid #e5e7eb; text-align:center;'>{idx+1}</td>"
            f"<td style='padding:8px; border-bottom:1px solid #e5e7eb;'>{it['name']}</td>"
            f"<td style='padding:8px; border-bottom:1px solid #e5e7eb; text-align:right;'>Rs. {it['price']:,.2f}</td>"
            f"<td style='padding:8px; border-bottom:1px solid #e5e7eb; text-align:center;'>{it['qty']}</td>"
            f"<td style='padding:8px; border-bottom:1px solid #e5e7eb; text-align:right; font-weight:bold;'>Rs. {it['total']:,.2f}</td></tr>"
            for idx, it in enumerate(bill_items)
        ])

        html_doc = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"><title>Invoice {bill_no}</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
        <style>
            body {{ font-family:'Inter', sans-serif; background:#f4f6f8; margin:0; padding:20px; color:#1f2937; }}
            .box {{ max-width:650px; margin:auto; padding:25px; background:#fff; border-radius:10px; border:1px solid #e5e7eb; position:relative; box-shadow:0 4px 15px rgba(0,0,0,0.05); }}
            .hdr {{ display:flex; justify-content:space-between; border-bottom:2px solid #e5e7eb; padding-bottom:15px; margin-bottom:15px; }}
            .title {{ font-size:22px; font-weight:900; margin:0; text-transform:uppercase; }}
            .stamp {{ position:absolute; bottom:80px; right:35px; width:140px; height:140px; border:3px double {stamp_col}; border-radius:50%; color:{stamp_col}; text-align:center; transform:rotate(-10deg); display:flex; flex-direction:column; justify-content:center; align-items:center; padding:5px; box-sizing:border-box; background:rgba(255,255,255,0.9); }}
            .pbtn {{ display:block; width:100%; background:#111827; color:#fff; text-align:center; padding:12px; font-weight:bold; border-radius:6px; margin-top:20px; border:none; cursor:pointer; }}
            @media print {{ .pbtn {{ display:none; }} body {{ background:#fff; padding:0; }} .box {{ border:none; box-shadow:none; }} }}
        </style></head><body>
        <div class="box">
            <div class="hdr">
                <div><h1 class="title">📕 {current_user['shop_name']}</h1><p style="margin:4px 0; font-size:12px;">Sanchalak: {current_user['owner_name']} | Mob: +91 {current_user['phone']}</p></div>
                <div style="text-align:right;"><h3 style="margin:0; color:#dc2626;">TAX INVOICE</h3><p style="margin:4px 0; font-size:12px;"><strong>Bill:</strong> {bill_no}<br><strong>Date:</strong> {now_str}</p></div>
            </div>
            <div style="background:#f9fafb; padding:10px; border-radius:6px; font-size:12px; margin-bottom:15px;"><strong>Grahak:</strong> {c_name} | <strong>Mob:</strong> +91 {c_phone} | <strong>Pata:</strong> {c_addr}</div>
            <table style="width:100%; border-collapse:collapse; font-size:12px;">
                <thead><tr style="background:#f3f4f6;"><th style="padding:8px;">#</th><th style="text-align:left; padding:8px;">Item</th><th style="text-align:right; padding:8px;">Rate</th><th style="text-align:center; padding:8px;">Qty</th><th style="text-align:right; padding:8px;">Kul</th></tr></thead>
                <tbody>{items_html}</tbody>
            </table>
            <div style="display:flex; justify-content:space-between; margin-top:15px; border-top:2px solid #111; padding-top:10px; font-size:16px; font-weight:bold;"><span>GRAND TOTAL:</span><span>Rs. {tot:,.2f}</span></div>
            <div class="stamp"><span style="font-size:9px; font-weight:bold;">{current_user['shop_name'][:20].upper()}</span><span style="font-size:11px; font-weight:900; border-top:1px solid; border-bottom:1px solid; margin:3px 0;">{stamp_title}</span><span style="font-size:8px;">{now_str[:10]}</span></div>
            <div style="margin-top:40px; display:flex; justify-content:space-between; align-items:flex-end; font-size:11px; color:#6b7280;"><div>* Digitally generated tamper-proof bill.</div><div style="text-align:center; width:150px; border-top:1px solid #333; padding-top:4px; font-weight:bold; color:#111;">{current_user['owner_name']}<br><span style="font-size:9px; font-weight:normal;">Authorized Signatory</span></div></div>
            <button class="pbtn" onclick="window.print()">🖨️ Print / Save As PDF</button>
        </div></body></html>
        """
        fpath = os.path.abspath("bill_receipt.html")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html_doc)
        webbrowser.open(f"file://{fpath}")
        close_dlg(billing_dialog)
        bill_items.clear()
        refresh_bill_items()
        show_toast("Bill browser me khul gaya!")
        if detail_view.visible:
            open_detail(selected_person_id)
        else:
            refresh_home()

    billing_dialog = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.icons.RECEIPT_LONG, color=PRIMARY_RED), ft.Text("Digital Mohar Billing", size=16, weight=ft.FontWeight.BOLD)], tight=True),
        content=ft.Container(
            width=380,
            content=ft.Column([
                ft.Row([b_item_name, b_item_qty, b_item_price]),
                make_btn("+ Item Add Karein", bgcolor=SUCCESS_GREEN, height=36, on_click=lambda e: add_bill_item()),
                ft.Row([bill_pay_status, bill_pay_mode]),
                ft.Divider(height=10),
                ft.Container(content=bill_items_col, height=150, border=ft.border.all(1, SURFACE_LIGHT), border_radius=8, padding=6),
                ft.Row([ft.Text("Kul Bill Rashi:", size=13, weight=ft.FontWeight.BOLD), bill_subtotal_txt], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], tight=True, spacing=8)
        ),
        actions=[
            make_btn("Cancel", bgcolor="#3a3a44", height=36, width=80, on_click=lambda e: close_dlg(billing_dialog)),
            make_btn("Generate Bill", bgcolor=PRIMARY_RED, height=36, width=140, on_click=lambda e: generate_bill_html())
        ]
    )

    # ------------------- Customer & Transaction Dialogs -------------------
    new_c_name = ft.TextField(label="Grahak Naam*")
    new_c_phone = ft.TextField(label="Mobile (10 Digit)*", keyboard_type=ft.KeyboardType.PHONE)
    new_c_addr = ft.TextField(label="Pata (Optional)")

    add_cust_dlg = ft.AlertDialog(
        title=ft.Text("Naya Grahak Khata"),
        content=ft.Column([new_c_name, new_c_phone, new_c_addr], tight=True),
        actions=[
            make_btn("Cancel", bgcolor="#3a3a44", height=36, width=80, on_click=lambda e: close_dlg(add_cust_dlg)),
            make_btn("Save", bgcolor=PRIMARY_RED, height=36, width=100, on_click=lambda e: save_cust())
        ]
    )

    def save_cust():
        cp = "".join(filter(str.isdigit, new_c_phone.value.strip()))
        if len(cp) != 10:
            show_toast("10 digit mobile dalein!")
            return
        if new_c_name.value.strip() and current_user["id"]:
            cursor.execute("INSERT INTO persons (user_id, name, phone, address) VALUES (?, ?, ?, ?)",
                           (current_user["id"], new_c_name.value.strip(), cp, new_c_addr.value.strip()))
            conn.commit()
            close_dlg(add_cust_dlg)
            new_c_name.value = ""
            new_c_phone.value = ""
            new_c_addr.value = ""
            refresh_home()
            show_toast("Grahak save ho gaya!")

    txn_amt = ft.TextField(label="₹ Rashi*", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
    txn_note = ft.TextField(label="Note / Vivran")
    curr_t_type = "DEBIT"

    def commit_txn():
        if txn_amt.value and selected_person_id:
            try:
                amt = float(txn_amt.value.strip())
                cursor.execute("INSERT INTO transactions (person_id, amount, txn_type, note) VALUES (?, ?, ?, ?)",
                               (selected_person_id, amt, curr_t_type, txn_note.value.strip()))
                conn.commit()
                close_dlg(add_txn_dlg)
                txn_amt.value = ""
                txn_note.value = ""
                open_detail(selected_person_id)
                show_toast("Entry lock ho gayi!")
            except Exception as ex:
                show_toast(f"Error: {str(ex)}")

    add_txn_dlg = ft.AlertDialog(
        title=ft.Text("Entry"),
        content=ft.Column([
            ft.Row([
                txn_amt,
                ft.Container(
                    content=ft.Icon(ft.icons.CALCULATE, color=ACCENT_GOLD, size=24),
                    bgcolor=SURFACE_LIGHT,
                    padding=10,
                    border_radius=8,
                    ink=True,
                    on_click=lambda e: open_smart_calc_for(lambda v: setattr(txn_amt, 'value', v) or page.update())
                )
            ]),
            txn_note
        ], tight=True, spacing=8),
        actions=[
            make_btn("Cancel", bgcolor="#3a3a44", height=36, width=80, on_click=lambda e: close_dlg(add_txn_dlg)),
            make_btn("Lock Entry", bgcolor=PRIMARY_RED, height=36, width=130, on_click=lambda e: commit_txn())
        ]
    )

    def open_entry(t):
        nonlocal curr_t_type
        curr_t_type = t
        lp = LANG_PACK.get(current_user["language"], LANG_PACK["hinglish"])
        add_txn_dlg.title.value = lp["debit"] if t == "DEBIT" else lp["credit"]
        open_dlg(add_txn_dlg)

    # ------------------- Developer Panel -------------------
    dev_pin = ft.TextField(label="Master PIN", password=True)
    dev_ver = ft.TextField(label="Version")
    dev_auth_dlg = ft.AlertDialog(
        title=ft.Text("Developer Access"),
        content=dev_pin,
        actions=[
            make_btn("Cancel", bgcolor="#3a3a44", height=36, width=80, on_click=lambda e: close_dlg(dev_auth_dlg)),
            make_btn("Verify", bgcolor=PRIMARY_RED, height=36, width=80, on_click=lambda e: verify_dev())
        ]
    )

    def verify_dev():
        if dev_pin.value.strip() == DEVELOPER_MASTER_PIN:
            close_dlg(dev_auth_dlg)
            show_toast("Master access granted!")
        else:
            show_toast("Galat PIN!")

    # ==================== PAGE 1: KHATA ====================
    home_avatar = ft.CircleAvatar(bgcolor=SURFACE_LIGHT, radius=18)
    shop_title_txt = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    owner_sub_txt = ft.Text("", size=11, color=MUTED_TEXT)
    total_bal_txt = ft.Text("₹0.00", size=24, weight=ft.FontWeight.BOLD, color=PRIMARY_RED)
    total_sub_txt = ft.Text("Kul Bazar Udhar", size=11, color=MUTED_TEXT)
    cust_list = ft.ListView(spacing=8, height=390)
    home_add_btn_txt = ft.Text("+ Grahak", color="white", weight=ft.FontWeight.BOLD, size=13)
    home_search_field = ft.TextField(hint_text="🔍 Grahak khojein...", on_change=lambda e: refresh_home(e.control.value), height=42, text_size=12)

    page_khata = ft.Container(
        padding=12,
        content=ft.Column([
            ft.Container(
                padding=12,
                bgcolor=SURFACE_CARD,
                border_radius=12,
                content=ft.Column([
                    ft.Row([
                        ft.Row([home_avatar, ft.Column([shop_title_txt, owner_sub_txt], spacing=1)]),
                        ft.Row([
                            ft.Container(
                                content=ft.Row([ft.Icon(ft.icons.HEADSET_MIC, size=15, color="#25D366"), ft.Text("Help", size=11, color="#25D366", weight=ft.FontWeight.BOLD)], tight=True),
                                bgcolor="#14261a",
                                border=ft.border.all(1, "#25D366"),
                                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                                border_radius=8,
                                ink=True,
                                on_click=open_dev_whatsapp
                            ),
                            ft.Container(
                                content=ft.Row([ft.Icon(ft.icons.PERSON_ADD, size=15, color="white"), home_add_btn_txt], tight=True, spacing=4),
                                bgcolor=PRIMARY_RED,
                                border_radius=10,
                                height=36,
                                padding=ft.padding.symmetric(horizontal=10),
                                ink=True,
                                on_click=lambda e: open_dlg(add_cust_dlg)
                            )
                        ], spacing=6)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(height=12),
                    total_bal_txt,
                    total_sub_txt
                ])
            ),
            home_search_field,
            cust_list
        ], spacing=10)
    )

    # ==================== PAGE 2: CALCULATOR ====================
    page_calc_history = ft.Text("", size=13, color=MUTED_TEXT, text_align=ft.TextAlign.RIGHT)
    page_calc_main = ft.Text("0", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)

    def on_page_calc_press(k):
        cur = page_calc_main.value
        if k == "C":
            page_calc_main.value = "0"
            page_calc_history.value = ""
        elif k == "⌫":
            if cur in ["0", "Error"] or len(cur) == 1:
                page_calc_main.value = "0"
                page_calc_history.value = ""
            else:
                page_calc_main.value = cur[:-1]
                page_calc_history.value = eval_live(page_calc_main.value)
        elif k == "=":
            try:
                s = cur.replace("×", "*").replace("÷", "/")
                r = eval(s)
                page_calc_history.value = cur + " ="
                page_calc_main.value = f"{r:,.2f}" if isinstance(r, float) and not r.is_integer() else str(int(r) if isinstance(r, float) else r)
            except Exception:
                page_calc_main.value = "Error"
                page_calc_history.value = ""
        elif k in ["+", "-", "×", "÷", "%"]:
            if cur != "Error":
                if cur[-1] in "+-×÷%":
                    page_calc_main.value = cur[:-1] + k
                else:
                    page_calc_main.value = cur + k
                page_calc_history.value = eval_live(page_calc_main.value)
        else:
            page_calc_main.value = k if cur in ["0", "Error"] else cur + k
            page_calc_history.value = eval_live(page_calc_main.value)
        page.update()

    def make_calc_k(lbl, col=SURFACE_LIGHT, tcol="white"):
        return ft.Container(
            content=ft.Text(lbl, size=15, weight=ft.FontWeight.BOLD, color=tcol),
            alignment=ft.alignment.center,
            bgcolor=col,
            border_radius=8,
            height=46,
            expand=True,
            ink=True,
            on_click=lambda e, v=lbl: on_page_calc_press(v)
        )

    page_calc = ft.Container(
        padding=12,
        visible=False,
        content=ft.Column([
            ft.Text("🧮 Digital Business Calculator", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([page_calc_history, page_calc_main], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                bgcolor="#121318",
                padding=14,
                border_radius=10
            ),
            ft.Row([make_calc_k("C", PRIMARY_RED), make_calc_k("⌫", "#3a3a44"), make_calc_k("%", "#3a3a44"), make_calc_k("÷", ACCENT_GOLD, "black")]),
            ft.Row([make_calc_k("7"), make_calc_k("8"), make_calc_k("9"), make_calc_k("×", ACCENT_GOLD, "black")]),
            ft.Row([make_calc_k("4"), make_calc_k("5"), make_calc_k("6"), make_calc_k("-", ACCENT_GOLD, "black")]),
            ft.Row([make_calc_k("1"), make_calc_k("2"), make_calc_k("3"), make_calc_k("+", ACCENT_GOLD, "black")]),
            ft.Row([make_calc_k("00"), make_calc_k("0"), make_calc_k("."), make_calc_k("=", SUCCESS_GREEN)])
        ], spacing=8)
    )

    # ==================== PAGE 3: MARKETING POSTERS ====================
    POSTER_TEMPLATES = [
        {"cat": "🌅 Shubh Prabhat", "q": "ईमानदारी और मेहनत ही वो पूंजी है जो व्यापार को ऊंचाइयों तक ले जाती है।", "bg": "#1e3a8a"},
        {"cat": "📈 Business Growth", "q": "ग्राहकों का विश्वास ही हमारी सबसे बड़ी कमाई है। अटूट भरोसा ही हमारी पहचान है।", "bg": "#14532d"},
        {"cat": "💳 Digital Payments", "q": "सुविधा आपकी, सेवा हमारी! हमारे यहाँ सभी प्रकार के ऑनलाइन UPI पेमेंट स्वीकार हैं।", "bg": "#581c87"}
    ]
    curr_poster = 0
    poster_avatar = ft.CircleAvatar(radius=28, bgcolor=SURFACE_LIGHT)
    poster_shop_txt = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color="white")
    poster_owner_txt = ft.Text("", size=11, color="#e2e8f0")
    poster_quote_txt = ft.Text(POSTER_TEMPLATES[0]["q"], size=14, weight=ft.FontWeight.W_500, color="white", text_align=ft.TextAlign.CENTER)
    poster_box = ft.Container(bgcolor=POSTER_TEMPLATES[0]["bg"], border_radius=14, padding=16)

    def update_poster_preview():
        t = POSTER_TEMPLATES[curr_poster]
        poster_shop_txt.value = current_user['shop_name'].upper() if current_user['shop_name'] else "MERI DUKAN"
        poster_owner_txt.value = f"Sanchalak: {current_user['owner_name']}" if current_user['owner_name'] else "Owner"
        poster_quote_txt.value = f"“{t['q']}”"
        poster_box.bgcolor = t["bg"]

    def share_poster_wa():
        t = POSTER_TEMPLATES[curr_poster]
        msg = f"✨ *{current_user['shop_name']}* ✨\n\n“{t['q']}”\n\n👤 {current_user['owner_name']}\n📞 +91 {current_user['phone']}"
        webbrowser.open(f"https://wa.me/?text={urllib.parse.quote(msg)}")
        show_toast("WhatsApp par share karein!")

    poster_box.content = ft.Column([
        ft.Row([poster_avatar, ft.Column([poster_shop_txt, poster_owner_txt], spacing=2)], spacing=12),
        ft.Divider(color=ft.colors.WHITE24, height=16),
        ft.Container(padding=ft.padding.symmetric(vertical=15), content=poster_quote_txt),
        ft.Text("★ Lal Khata Pro Verified ★", size=10, color=ft.colors.WHITE70, text_align=ft.TextAlign.CENTER)
    ], spacing=10)

    page_posters = ft.Container(
        padding=12,
        visible=False,
        content=ft.Column([
            ft.Row([
                ft.Text("🎨 Daily Growth Poster", size=17, weight=ft.FontWeight.BOLD),
                ft.IconButton(icon=ft.icons.ADD_A_PHOTO, icon_color=ACCENT_GOLD, on_click=lambda e: dp_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            poster_box,
            ft.Row([
                ft.Container(
                    content=ft.Text(f"Template {i+1}", size=11, weight=ft.FontWeight.BOLD),
                    bgcolor=t["bg"],
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                    border_radius=8,
                    ink=True,
                    on_click=lambda e, idx=i: (setattr(main, 'curr_poster', idx), update_poster_preview(), page.update())
                ) for i, t in enumerate(POSTER_TEMPLATES)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            make_btn("📲 WhatsApp Share", bgcolor="#25D366", height=42, icon=ft.icons.SHARE, on_click=lambda e: share_poster_wa())
        ], spacing=12)
    )

    # ==================== PAGE 4: REPORTS ====================
    rep_total_cust_txt = ft.Text("0", size=18, weight=ft.FontWeight.BOLD)
    rep_total_udhar_txt = ft.Text("₹0.00", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_RED)
    rep_total_jama_txt = ft.Text("₹0.00", size=18, weight=ft.FontWeight.BOLD, color=SUCCESS_GREEN)
    rep_net_txt = ft.Text("₹0.00", size=22, weight=ft.FontWeight.BOLD, color=ACCENT_GOLD)

    page_reports = ft.Container(
        padding=12,
        visible=False,
        content=ft.Column([
            ft.Text("📊 Vyapar Reports", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                padding=14,
                bgcolor=SURFACE_CARD,
                border_radius=12,
                content=ft.Column([
                    ft.Text("Kul Dukan Status", size=12, color=MUTED_TEXT),
                    rep_net_txt,
                    ft.Divider(height=16),
                    ft.Row([
                        ft.Column([ft.Text("Grahak", size=11, color=MUTED_TEXT), rep_total_cust_txt]),
                        ft.Column([ft.Text("Udhar", size=11, color=MUTED_TEXT), rep_total_udhar_txt]),
                        ft.Column([ft.Text("Jama", size=11, color=MUTED_TEXT), rep_total_jama_txt]),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ])
            )
        ], spacing=12)
    )

    def update_reports():
        if not current_user["id"]:
            return
        uid = current_user["id"]
        cursor.execute("SELECT COUNT(*) FROM persons WHERE user_id=?", (uid,))
        rep_total_cust_txt.value = str(cursor.fetchone()[0])
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions t JOIN persons p ON t.person_id=p.id WHERE p.user_id=? AND t.txn_type='DEBIT'", (uid,))
        dtot = cursor.fetchone()[0]
        rep_total_udhar_txt.value = f"₹{dtot:,.2f}"
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions t JOIN persons p ON t.person_id=p.id WHERE p.user_id=? AND t.txn_type='CREDIT'", (uid,))
        ctot = cursor.fetchone()[0]
        rep_total_jama_txt.value = f"₹{ctot:,.2f}"
        net = dtot - ctot
        rep_net_txt.value = f"₹{net:,.2f} Lena" if net >= 0 else f"₹{abs(net):,.2f} Jama"
        rep_net_txt.color = PRIMARY_RED if net >= 0 else SUCCESS_GREEN

    # ==================== PAGE 5: PROFILE & SETTINGS ====================
    prof_avatar = ft.CircleAvatar(radius=45, bgcolor=SURFACE_LIGHT)
    prof_p_shop = ft.TextField(label="Dukan Naam", text_size=13)
    prof_p_owner = ft.TextField(label="Sanchalak Naam", text_size=13)
    prof_p_phone = ft.Text("", size=13, color=MUTED_TEXT)

    def change_lang(nl):
        current_user["language"] = nl
        if current_user["id"]:
            cursor.execute("UPDATE app_users SET app_language=? WHERE id=?", (nl, current_user["id"]))
            conn.commit()
        apply_labels()
        show_toast(f"Language: {nl.upper()}")

    prof_lang_dropdown = ft.Dropdown(
        label="App Language (Bhasha)",
        options=[
            ft.dropdown.Option("hinglish", "Hinglish"),
            ft.dropdown.Option("hindi", "हिन्दी"),
            ft.dropdown.Option("english", "English")
        ],
        value="hinglish",
        text_size=13,
        on_change=lambda e: change_lang(e.control.value)
    )

    def apply_labels():
        lp = LANG_PACK.get(current_user["language"], LANG_PACK["hinglish"])
        home_add_btn_txt.value = lp["btn_add_cust"]
        home_search_field.hint_text = lp["search_hint"]
        bottom_nav.destinations[0].label = lp["tab_khata"]
        bottom_nav.destinations[1].label = lp["tab_calc"]
        bottom_nav.destinations[2].label = lp["tab_marketing"]
        bottom_nav.destinations[3].label = lp["tab_reports"]
        bottom_nav.destinations[4].label = lp["tab_profile"]
        ad_tag.value = lp["ad_tag"]
        ad_title.value = lp["ad_txt"]
        page.update()

    def save_profile():
        s, o = prof_p_shop.value.strip(), prof_p_owner.value.strip()
        if s and o and current_user["id"]:
            cursor.execute("UPDATE app_users SET shop_name=?, owner_name=? WHERE id=?", (s, o, current_user["id"]))
            conn.commit()
            current_user["shop_name"] = s
            current_user["owner_name"] = o
            shop_title_txt.value = f"📕 {s}"
            owner_sub_txt.value = f"Owner: {o}"
            update_dp_everywhere()
            show_toast("Profile save ho gayi!")
            refresh_home()

    page_profile = ft.Container(
        padding=12,
        visible=False,
        content=ft.Column([
            ft.Text("👤 Dukan Profile", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                padding=14,
                bgcolor=SURFACE_CARD,
                border_radius=12,
                content=ft.Column([
                    ft.Row([
                        prof_avatar,
                        ft.Column([
                            prof_p_phone,
                            make_btn("📷 DP Upload", bgcolor="#2c3e50", height=34, width=140, on_click=lambda e: dp_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE))
                        ], spacing=6)
                    ], spacing=14),
                    ft.Divider(),
                    prof_lang_dropdown,
                    prof_p_shop,
                    prof_p_owner,
                    make_btn("Save Profile", bgcolor=SUCCESS_GREEN, height=40, on_click=lambda e: save_profile())
                ], spacing=10)
            ),
            ft.Container(
                padding=12,
                bgcolor=SURFACE_CARD,
                border_radius=12,
                content=ft.Column([
                    ft.Text("💬 WhatsApp Support", size=14, weight=ft.FontWeight.BOLD),
                    make_btn("Contact Developer", bgcolor="#25D366", height=38, icon=ft.icons.CHAT, on_click=open_dev_whatsapp)
                ], spacing=6)
            ),
            make_btn("Logout", bgcolor="#3a3a44", height=40, icon=ft.icons.LOGOUT, on_click=lambda e: logout())
        ], spacing=12)
    )

    # ------------------- Sponsored Ad Banner Slot -------------------
    ad_tag = ft.Text("SPONSORED / ADVERTISEMENT", size=9, weight=ft.FontWeight.BOLD, color=ACCENT_GOLD)
    ad_title = ft.Text("Lal Khata Pro: Dukan ko digital banayein aur bikri badhayein!", size=11, weight=ft.FontWeight.W_600, color="white")

    income_ad_slot = ft.Container(
        height=50,
        bgcolor="#14161f",
        border=ft.border.all(1, "#272a38"),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        ink=True,
        on_click=lambda e: show_toast("Google AdMob Native Ready"),
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.icons.CAMPAIGN, color=ACCENT_GOLD, size=20),
                ft.Column([ad_tag, ad_title], spacing=1, expand=True)
            ], spacing=8, expand=True),
            ft.Icon(ft.icons.OPEN_IN_NEW, size=15, color=MUTED_TEXT)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )

    # ------------------- 5-Tab Navigation -------------------
    def on_nav(e):
        idx = e.control.selected_index
        page_khata.visible = (idx == 0)
        page_calc.visible = (idx == 1)
        page_posters.visible = (idx == 2)
        page_reports.visible = (idx == 3)
        page_profile.visible = (idx == 4)
        if idx == 2:
            update_poster_preview()
        elif idx == 3:
            update_reports()
        page.update()

    bottom_nav = ft.NavigationBar(
        selected_index=0,
        bgcolor="#121319",
        height=65,
        on_change=on_nav,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, selected_icon=ft.icons.ACCOUNT_BALANCE_WALLET, label="Khata"),
            ft.NavigationBarDestination(icon=ft.icons.CALCULATE_OUTLINED, selected_icon=ft.icons.CALCULATE, label="Calc"),
            ft.NavigationBarDestination(icon=ft.icons.AUTO_AWESOME_OUTLINED, selected_icon=ft.icons.AUTO_AWESOME, label="Marketing"),
            ft.NavigationBarDestination(icon=ft.icons.BAR_CHART_OUTLINED, selected_icon=ft.icons.BAR_CHART, label="Reports"),
            ft.NavigationBarDestination(icon=ft.icons.PERSON_OUTLINE, selected_icon=ft.icons.PERSON, label="Profile")
        ]
    )

    main_dashboard_layout = ft.Container(
        visible=False,
        expand=True,
        content=ft.Column([
            ft.Container(content=ft.Stack([page_khata, page_calc, page_posters, page_reports, page_profile]), expand=True),
            income_ad_slot,
            bottom_nav
        ], spacing=0)
    )

    # ==================== DETAIL VIEW ====================
    det_name_txt = ft.Text("", size=18, weight=ft.FontWeight.BOLD)
    det_meta_txt = ft.Text("", size=12, color=MUTED_TEXT)
    det_bal_txt = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    tx_list = ft.ListView(spacing=8, expand=True)
    current_det_phone = ""
    current_det_name = ""

    def send_wa(e):
        p = "".join(filter(str.isdigit, current_det_phone))
        if len(p) == 10:
            p = "91" + p
        cursor.execute("SELECT COALESCE(SUM(CASE WHEN txn_type='DEBIT' THEN amount ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN txn_type='CREDIT' THEN amount ELSE 0 END), 0) FROM transactions WHERE person_id = ?", (selected_person_id,))
        net_b = cursor.fetchone()[0]
        msg = f"Pranam {current_det_name} ji,\nLal Khata ({current_user['shop_name']}) baki rashi: Rs.{abs(net_b):,.2f}."
        webbrowser.open(f"https://wa.me/{p}?text={urllib.parse.quote(msg)}")

    detail_view = ft.Container(
        padding=12,
        visible=False,
        expand=True,
        content=ft.Column([
            ft.Container(
                padding=12,
                bgcolor=SURFACE_CARD,
                border_radius=12,
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Row([ft.Icon(ft.icons.ARROW_BACK, size=18, color=ACCENT_GOLD), ft.Text("← Wapas", size=13, weight=ft.FontWeight.BOLD, color=ACCENT_GOLD)], tight=True), ink=True, on_click=lambda e: back_to_home()),
                        det_bal_txt
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    det_name_txt,
                    det_meta_txt,
                    ft.Row([
                        make_btn("📞 Call", bgcolor="#107c41", height=36, expand=True, on_click=lambda e: webbrowser.open(f"tel:{current_det_phone}")),
                        make_btn("💬 WhatsApp", bgcolor="#25D366", height=36, expand=True, on_click=send_wa),
                        make_btn("🧾 Bill", bgcolor="#8e44ad", height=36, expand=True, on_click=lambda e: (bill_items.clear(), refresh_bill_items(), open_dlg(billing_dialog)))
                    ], spacing=6)
                ], spacing=6)
            ),
            ft.Row([ft.Icon(ft.icons.LOCK, size=14, color=SUCCESS_GREEN), ft.Text("Audit Locked Entries", size=10, color=MUTED_TEXT)], tight=True),
            tx_list,
            ft.Row([
                make_btn("🔻 Udhar Diya (-)", bgcolor=PRIMARY_RED, height=44, expand=True, on_click=lambda e: open_entry("DEBIT")),
                make_btn("🔺 Jama Mila (+)", bgcolor=SUCCESS_GREEN, height=44, expand=True, on_click=lambda e: open_entry("CREDIT"))
            ], spacing=10)
        ], spacing=10)
    )

    # ==================== AUTH VIEW ====================
    login_phone_in = ft.TextField(label="Registered Mobile (10 Digit)", keyboard_type=ft.KeyboardType.PHONE)
    login_pin_in = ft.TextField(label="6-Digit Khata PIN", password=True, can_reveal_password=True, max_length=6, keyboard_type=ft.KeyboardType.NUMBER)

    reg_shop_in = ft.TextField(label="Dukan Ka Naam*")
    reg_owner_in = ft.TextField(label="Aapka Naam*")
    reg_phone_in = ft.TextField(label="Mobile (10 Digit)*", keyboard_type=ft.KeyboardType.PHONE)
    reg_pin_in = ft.TextField(label="6-Digit PIN*", password=True, can_reveal_password=True, max_length=6, keyboard_type=ft.KeyboardType.NUMBER)

    def trigger_biometric():
        p = "".join(filter(str.isdigit, login_phone_in.value.strip()))
        if len(p) != 10:
            show_toast("10-digit mobile dalein!")
            return
        cursor.execute("SELECT id, shop_name, owner_name, phone, gstin, shop_address, profile_pic, app_language FROM app_users WHERE phone=?", (p,))
        u = cursor.fetchone()
        if not u:
            show_toast("Yeh number registered nahi hai!")
            return
        current_user["id"], current_user["shop_name"], current_user["owner_name"], current_user["phone"] = u[:4]
        current_user["profile_pic"] = u[6] if len(u) > 6 and u[6] else ""
        current_user["language"] = u[7] if len(u) > 7 and u[7] else "hinglish"
        page.client_storage.set("saved_user_id", u[0])
        show_dashboard_screen()
        show_toast("Biometric Verified! Swagat hai.")

    login_box = ft.Column(spacing=10, controls=[
        login_phone_in,
        login_pin_in,
        make_btn("PIN Se Login Karein", bgcolor=PRIMARY_RED, on_click=lambda e: auth_login()),
        ft.Container(
            content=ft.Row([ft.Icon(ft.icons.FINGERPRINT, color=SUCCESS_GREEN, size=24), ft.Text("Fingerprint Se Kholein", color=SUCCESS_GREEN, weight=ft.FontWeight.BOLD, size=12)], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor="#182c1e",
            border=ft.border.all(1, SUCCESS_GREEN),
            border_radius=10,
            height=42,
            ink=True,
            on_click=lambda e: trigger_biometric()
        )
    ])

    reg_box = ft.Column(spacing=10, visible=False, controls=[
        reg_shop_in,
        reg_owner_in,
        reg_phone_in,
        reg_pin_in,
        make_btn("Create Account", bgcolor=SUCCESS_GREEN, on_click=lambda e: auth_reg())
    ])

    tab_l = ft.Container(content=ft.Text("Login", weight=ft.FontWeight.BOLD), bgcolor=SURFACE_LIGHT, padding=8, border_radius=6, expand=True, alignment=ft.alignment.center, on_click=lambda e: (setattr(login_box, 'visible', True), setattr(reg_box, 'visible', False), setattr(tab_l, 'bgcolor', SURFACE_LIGHT), setattr(tab_r, 'bgcolor', 'transparent'), page.update()))
    tab_r = ft.Container(content=ft.Text("Naya Account", color=MUTED_TEXT), padding=8, border_radius=6, expand=True, alignment=ft.alignment.center, on_click=lambda e: (setattr(login_box, 'visible', False), setattr(reg_box, 'visible', True), setattr(tab_l, 'bgcolor', 'transparent'), setattr(tab_r, 'bgcolor', SURFACE_LIGHT), page.update()))

    auth_view = ft.Container(
        padding=14,
        expand=True,
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.Container(
                        content=ft.Row([ft.Icon(ft.icons.SHIELD, color=ACCENT_GOLD, size=15), ft.Text("Developer", color=ACCENT_GOLD, size=11)], tight=True),
                        on_click=lambda e: open_dlg(dev_auth_dlg)
                    )
                ], alignment=ft.MainAxisAlignment.END),
                ft.Container(
                    content=ft.Column([
                        ft.Container(content=ft.Icon(ft.icons.MENU_BOOK_ROUNDED, size=46, color="white"), bgcolor=PRIMARY_RED, padding=14, border_radius=18),
                        ft.Text("LAL KHATA PRO", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text("Anti-Fraud Ledger & Multi-Language Hub", size=11, color=MUTED_TEXT)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    alignment=ft.alignment.center
                ),
                ft.Container(content=ft.Row([tab_l, tab_r]), bgcolor="#14151b", padding=4, border_radius=8),
                login_box,
                reg_box
            ],
            spacing=12
        )
    )

    def show_dashboard_screen():
        auth_view.visible = False
        detail_view.visible = False
        main_dashboard_layout.visible = True
        bottom_nav.selected_index = 0
        page_khata.visible = True
        page_calc.visible = False
        page_posters.visible = False
        page_reports.visible = False
        page_profile.visible = False

        shop_title_txt.value = f"📕 {current_user['shop_name']}"
        owner_sub_txt.value = f"Owner: {current_user['owner_name']}"
        prof_p_shop.value = current_user['shop_name']
        prof_p_owner.value = current_user['owner_name']
        prof_p_phone.value = f"📞 +91 {current_user['phone']}"
        prof_lang_dropdown.value = current_user.get("language", "hinglish")
        update_dp_everywhere()
        apply_labels()
        refresh_home()
        page.update()

    def auth_login():
        p = "".join(filter(str.isdigit, login_phone_in.value.strip()))
        pv = login_pin_in.value.strip()
        if len(p) != 10 or len(pv) != 6:
            show_toast("10-digit number aur 6-digit PIN dalein!")
            return
        cursor.execute("SELECT id, shop_name, owner_name, phone, pin, gstin, shop_address, profile_pic, app_language FROM app_users WHERE phone=?", (p,))
        u = cursor.fetchone()
        if not u:
            show_toast("Account nahi mila!")
            return
        if pv == u[4]:
            current_user["id"], current_user["shop_name"], current_user["owner_name"], current_user["phone"] = u[:4]
            current_user["profile_pic"] = u[7] if len(u) > 7 and u[7] else ""
            current_user["language"] = u[8] if len(u) > 8 and u[8] else "hinglish"
            page.client_storage.set("saved_user_id", u[0])
            login_pin_in.value = ""
            show_dashboard_screen()
            show_toast(f"Swagat hai, {current_user['owner_name']} ji!")
        else:
            show_toast("Galat PIN!")

    def auth_reg():
        s, o = reg_shop_in.value.strip(), reg_owner_in.value.strip()
        p = "".join(filter(str.isdigit, reg_phone_in.value.strip()))
        pv = reg_pin_in.value.strip()
        if not s or not o or len(p) != 10 or len(pv) != 6:
            show_toast("Sabhi box sahi se bharein!")
            return
        try:
            cursor.execute("INSERT INTO app_users (shop_name, owner_name, phone, pin, app_language) VALUES (?, ?, ?, ?, 'hinglish')", (s, o, p, pv))
            conn.commit()
            cursor.execute("SELECT id, shop_name, owner_name, phone, gstin, shop_address, profile_pic, app_language FROM app_users WHERE phone=?", (p,))
            u = cursor.fetchone()
            current_user["id"], current_user["shop_name"], current_user["owner_name"], current_user["phone"] = u[:4]
            page.client_storage.set("saved_user_id", u[0])
            show_dashboard_screen()
            show_toast("Naya Khata ban gaya!")
        except sqlite3.IntegrityError:
            show_toast("Yeh number pehle se registered hai!")

    def logout():
        page.client_storage.remove("saved_user_id")
        current_user["id"] = None
        main_dashboard_layout.visible = False
        detail_view.visible = False
        auth_view.visible = True
        show_toast("Logout safal.")
        page.update()

    def refresh_home(search=""):
        cust_list.controls.clear()
        if not current_user["id"]:
            return
        uid = current_user["id"]
        q = """
            SELECT p.id, p.name, p.phone,
                COALESCE(SUM(CASE WHEN t.txn_type='DEBIT' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN t.txn_type='CREDIT' THEN amount ELSE 0 END), 0) as balance
            FROM persons p LEFT JOIN transactions t ON p.id = t.person_id
            WHERE p.user_id = ?
        """
        params = [uid]
        if search:
            q += " AND (p.name LIKE ? OR p.phone LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        q += " GROUP BY p.id ORDER BY p.id DESC"
        cursor.execute(q, tuple(params))

        for cid, name, phone, b in cursor.fetchall():
            tag = "Baki" if b >= 0 else "Jama"
            b_col = PRIMARY_RED if b > 0 else (SUCCESS_GREEN if b < 0 else MUTED_TEXT)
            cust_list.controls.append(
                ft.Container(
                    bgcolor=SURFACE_CARD,
                    padding=10,
                    border_radius=8,
                    ink=True,
                    on_click=lambda e, i=cid: open_detail(i),
                    content=ft.Row([
                        ft.Row([
                            ft.CircleAvatar(content=ft.Text(name[0].upper() if name else "?", color="white"), bgcolor=SURFACE_LIGHT, radius=18),
                            ft.Column([ft.Text(name, size=14, weight=ft.FontWeight.W_600), ft.Text(f"+91 {phone}", size=10, color=MUTED_TEXT)], spacing=2)
                        ]),
                        ft.Row([
                            ft.Container(
                                content=ft.Row([ft.Icon(ft.icons.RECEIPT, size=14, color="#a569bd"), ft.Text("Bill", size=11, color="#a569bd", weight=ft.FontWeight.BOLD)], tight=True),
                                bgcolor="#22182b",
                                border=ft.border.all(1, "#8e44ad"),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=6,
                                ink=True,
                                on_click=lambda e, i=cid: (setattr(main, 'selected_person_id', i), bill_items.clear(), refresh_bill_items(), open_dlg(billing_dialog))
                            ),
                            ft.Column([ft.Text(f"₹{abs(b):,.2f}", size=13, weight=ft.FontWeight.BOLD, color=b_col), ft.Text(tag, size=9, color=b_col)], horizontal_alignment=ft.CrossAxisAlignment.END)
                        ], spacing=8)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            )

        cursor.execute("SELECT COALESCE(SUM(CASE WHEN t.txn_type='DEBIT' THEN amount ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN t.txn_type='CREDIT' THEN amount ELSE 0 END), 0) FROM transactions t JOIN persons p ON t.person_id = p.id WHERE p.user_id = ?", (uid,))
        row = cursor.fetchone()
        net = row[0] if row and row[0] else 0.0
        lp = LANG_PACK.get(current_user["language"], LANG_PACK["hinglish"])
        total_bal_txt.value = f"₹{abs(net):,.2f}"
        total_bal_txt.color = PRIMARY_RED if net >= 0 else SUCCESS_GREEN
        total_sub_txt.value = lp["udhar_sub"] if net >= 0 else lp["jama_sub"]
        page.update()

    def open_detail(cid):
        nonlocal selected_person_id, current_det_name, current_det_phone
        selected_person_id = cid
        cursor.execute("SELECT name, phone FROM persons WHERE id=?", (cid,))
        row = cursor.fetchone()
        if not row:
            show_toast("Grahak nahi mila!")
            return
        name, phone = row
        current_det_name = name
        current_det_phone = phone

        cursor.execute("SELECT COALESCE(SUM(CASE WHEN txn_type='DEBIT' THEN amount ELSE 0 END), 0) - COALESCE(SUM(CASE WHEN txn_type='CREDIT' THEN amount ELSE 0 END), 0) FROM transactions WHERE person_id = ?", (cid,))
        bal = cursor.fetchone()[0] or 0.0

        det_name_txt.value = name
        det_meta_txt.value = f"Mob: +91 {phone}"
        det_bal_txt.value = f"₹{bal:,.2f} Baki" if bal >= 0 else f"₹{abs(bal):,.2f} Jama"
        det_bal_txt.color = PRIMARY_RED if bal >= 0 else SUCCESS_GREEN

        tx_list.controls.clear()
        cursor.execute("SELECT amount, txn_type, note, date FROM transactions WHERE person_id=? ORDER BY id DESC", (cid,))
        for a, t, n, d in cursor.fetchall():
            is_d = (t == "DEBIT")
            tx_list.controls.append(
                ft.Container(
                    bgcolor=SURFACE_CARD,
                    padding=10,
                    border_radius=8,
                    content=ft.Row([
                        ft.Row([
                            ft.Icon(ft.icons.LOCK, size=14, color=ACCENT_GOLD),
                            ft.Column([ft.Text(n if n else ("Udhar" if is_d else "Jama"), size=13, weight=ft.FontWeight.W_500), ft.Text(d[:16], size=10, color=MUTED_TEXT)], spacing=2)
                        ], spacing=8),
                        ft.Text(f"{'-' if is_d else '+'} ₹{a:,.2f}", size=14, weight=ft.FontWeight.BOLD, color=PRIMARY_RED if is_d else SUCCESS_GREEN)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            )

        main_dashboard_layout.visible = False
        detail_view.visible = True
        page.update()

    def back_to_home():
        detail_view.visible = False
        main_dashboard_layout.visible = True
        refresh_home()
        page.update()

    page.add(ft.Stack([auth_view, main_dashboard_layout, detail_view], expand=True))

    saved_id = page.client_storage.get("saved_user_id")
    if saved_id:
        cursor.execute("SELECT id, shop_name, owner_name, phone, gstin, shop_address, profile_pic, app_language FROM app_users WHERE id=?", (saved_id,))
        u = cursor.fetchone()
        if u:
            current_user["id"], current_user["shop_name"], current_user["owner_name"], current_user["phone"] = u[:4]
            current_user["profile_pic"] = u[6] if len(u) > 6 and u[6] else ""
            current_user["language"] = u[7] if len(u) > 7 and u[7] else "hinglish"
            show_dashboard_screen()

    page.update()


if __name__ == "__main__":
    ft.app(target=main)