import flet as ft
import websocket
import json
import threading

def main(page: ft.Page):
    page.title = "Academia Innova - Dashboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # UI Elements for Telemetry Data
    status_text = ft.Text("Sistem Activ", color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD)
    battery_bar = ft.ProgressBar(width=300, value=0.0, color=ft.Colors.GREEN_500, bgcolor=ft.Colors.GREY_300)
    battery_text = ft.Text("0%", size=20, weight=ft.FontWeight.BOLD)
    
    current_text = ft.Text("0.00 A", size=18)
    power_text = ft.Text("0.00 kW", size=18)
    energy_text = ft.Text("0.00 kWh", size=18)

    # UI Elements for Account Details
    user_avatar = ft.Icon(ft.Icons.PERSON, color=ft.Colors.GREEN_800, size=30)
    user_name_text = ft.Text("Așteptare scanare...", size=16, weight=ft.FontWeight.W_500)
    vehicle_text = ft.Text("Vehicul: nescanat", size=14, color=ft.Colors.GREY_600)

    # Main Card Layout Container
    page.add(
        ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Stație Încărcare", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                        ft.Divider(),
                        
                        # Account Profile Card Container (Fixed Casing syntax)
                        ft.Container(
                            content=ft.Row([
                                user_avatar,
                                ft.Column([user_name_text, vehicle_text], spacing=2)
                            ]),
                            bgcolor=ft.Colors.GREY_100,
                            padding=12,
                            border_radius=8,
                            margin=ft.Margin.only(bottom=10)
                        ),
                        
                        battery_text,
                        battery_bar,
                        ft.Row([ft.Text("Curent:"), current_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text("Putere:"), power_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([ft.Text("Energie:"), energy_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(status_text, bgcolor=ft.Colors.GREEN_50, padding=10, border_radius=5)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                ),
                padding=25,
                width=350,
            )
        )
    )

    def ws_listener():
        # NOTE: Change '127.0.0.1' to your actual laptop Wi-Fi IP address for smartphone browser testing
        ws_url = "ws://10.189.15.212:8090/ws/browser" 
        try:
            ws = websocket.create_connection(ws_url)
            while True:
                result = ws.recv()
                data = json.loads(result)
                
                # Update visual telemetry metrics
                battery_bar.value = data.get("soc", 0) / 100.0
                battery_text.value = f"{data.get('soc', 0)}%"
                current_text.value = f"{data.get('current', 0.0):.2f} A"
                power_text.value = f"{data.get('power', 0.0):.2f} kW"
                energy_text.value = f"{data.get('energy', 0.0):.2f} kWh"
                
                # Update user account fields over the stream
                user_name_text.value = data.get("user_name", "Așteptare scanare...")
                vehicle_text.value = f"Vehicul: {data.get('vehicle', 'Nespecificat')}"
                
                page.update()
        except Exception as e:
            status_text.value = "Eroare Conexiune"
            status_text.color = ft.Colors.RED_700
            page.update()

    threading.Thread(target=ws_listener, daemon=True).start()

ft.run(main, view=ft.AppView.WEB_BROWSER, port=8500, host="0.0.0.0")