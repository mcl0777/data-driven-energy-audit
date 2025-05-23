import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

def find_totalpower_column(df):
    """
    Find the columns with the highest sum of values, assuming these are total power column.
    """
    return df.iloc[:, 1:].sum().idxmax()

def create_energy_audit_pdf(machine_info, standby_data=None, ready_data=None, process_data=None, percentages=None, output_path='energieeinsparungsaudit.pdf'):
    # Unpack machine information
    company = machine_info.get('company')
    model = machine_info.get('model')
    location = machine_info.get('location')
    date = machine_info.get('date')
    time = machine_info.get('time')

    # Ensure percentages are in numeric form
    if percentages:
        operating_time_percentage = {
            "Stand-By": float(percentages.get("standby", 0.15)) / 100,
            "Ready": float(percentages.get("ready", 0.05)) / 100,
            "Prozess": float(percentages.get("process", 0.60)) / 100
        }
    else:
        operating_time_percentage = {
            "Stand-By": 0.15,
            "Ready": 0.05,
            "Prozess": 0.60
        }

    # Create a PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    # Add machine info
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleStyle', fontSize=16, leading=20, spaceAfter=20, alignment=1))
    styles.add(ParagraphStyle(name='SubtitleStyle', fontSize=12, leading=14, spaceAfter=14, alignment=0))
    styles.add(ParagraphStyle(name='NormalStyle', fontSize=10, leading=12, spaceAfter=12, alignment=0))

    title = Paragraph("<b>Datenbasiertes Energieeinsparungsaudit</b>", styles['TitleStyle'])
    elements.append(title)

    machine_info_paragraph = f"""
    <b>Unternehmen:</b> {company}<br/>
    <b>Modell:</b> {model}<br/>
    <b>Standort:</b> {location}<br/>
    <b>Datum:</b> {date}<br/>
    <b>Uhrzeit:</b> {time}<br/>
    """
    elements.append(Paragraph(machine_info_paragraph, styles['NormalStyle']))
    elements.append(Spacer(1, 14))

    # Function to add a chart to the PDF
    def add_chart_to_pdf(chart):
        imgdata = io.BytesIO()
        chart.savefig(imgdata, format='png', dpi=200, bbox_inches='tight')
        imgdata.seek(0)
        img = Image(imgdata)
        img.drawHeight = 2.5 * inch
        img.drawWidth = 4.5 * inch
        return img

    # Function to calculate key metrics
    def calculate_metrics(data, time_column, power_column):
        mean_power = data[power_column].mean()
        peak_power = data[power_column].max()
        min_power = data[power_column].min()
        total_energy = (data[power_column] * (data[time_column].diff().fillna(0))).sum() / (3600 * 1000)  # Energy in kWh
        return mean_power, peak_power, min_power, total_energy

    # Function to convert RGBA to Hex
    def rgba_to_hex(rgba):
        return to_hex(rgba)

    # Function to create a pie chart
    def add_pie_chart_to_pdf(labels, sizes, title):
        fig, ax = plt.subplots(figsize=(4, 4))
        wedges, _ = ax.pie(sizes, startangle=90, colors=plt.cm.Paired.colors, wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'})
        ax.set_aspect('equal')  # Ensure the pie chart is a perfect circle
        ax.set_title(title)

        legend_texts = [f'<font color="{rgba_to_hex(wedges[i].get_facecolor())}">{labels[i]}: {sizes[i]:.2f}%</font>' for i in range(len(labels))]
        legend_paragraph = Paragraph('<br/>'.join(legend_texts), styles['NormalStyle'])

        plt.close(fig)
        return add_chart_to_pdf(fig), legend_paragraph

    # Initialize storage for comparison and forecast tables
    comparison_data = [['Zustand', 'Mittlere Leistung (W)', 'Maximale Leistung (W)', 'Minimale Leistung (W)', 'Energieverbrauch (kWh)']]
    forecast_data = [['Zustand', 'Prozentsatz der Betriebszeit', 'Energieverbrauch (kWh) im Jahr']]
    hours_per_year = 230 * 8  # Total hours in a year (230 Tage * 8 Stunden)

    # Add charts and metrics for each state
    states = {
        "Stand-By": standby_data,
        "Ready": ready_data,
        "Prozess": process_data
    }

    for state, df in states.items():
        if df is not None:
            # Identify the time and power columns
            time_column = df.columns[0]
            total_energy_column = find_totalpower_column(df)
            power_columns = [col for col in df.columns if col not in [time_column, total_energy_column]]

            # Add subtitle
            subtitle = Paragraph(f"<b>Zustand: {state}</b>", styles['SubtitleStyle'])
            elements.append(subtitle)

            # Plot energy curves for each component
            table_data = []
            pie_labels = []
            pie_sizes = []

            for component in power_columns:
                plt.figure(figsize=(6, 4))  # Set the figure size
                plt.plot(df[time_column], df[component])
                plt.title(component)
                plt.xlabel('Zeit [s]')
                plt.ylabel('Leistung [W]')
                chart = add_chart_to_pdf(plt)
                plt.close()

                # Calculate key metrics
                mean_power, peak_power, min_power, total_energy = calculate_metrics(df, time_column, component)
                metrics_paragraph = f"""
                <b>Mittlere Leistungsaufnahme:</b> {mean_power:.2f} W<br/>
                <b>Maximale Leistung:</b> {peak_power:.2f} W<br/>
                <b>Minimale Leistung:</b> {min_power:.2f} W<br/>
                <b>Energieverbrauch pro Betriebsstunde:</b> {total_energy:.2f} kWh<br/>
                """
                metrics = Paragraph(metrics_paragraph, styles['NormalStyle'])

                # Add chart and metrics to the table
                table_data.append([chart, metrics])

                # Add data for pie chart
                average_power = df[component].mean()
                pie_labels.append(component)
                pie_sizes.append(average_power)

            # Plot and add energy curve for total energy
            plt.figure(figsize=(6, 4))
            plt.plot(df[time_column], df[total_energy_column])
            plt.title(f'Gesamtenergie - {state}')
            plt.xlabel('Zeit [s]')
            plt.ylabel('Leistung [W]')
            total_energy_chart = add_chart_to_pdf(plt)
            plt.close()

            # Calculate key metrics for total energy
            mean_power, peak_power, min_power, total_energy = calculate_metrics(df, time_column, total_energy_column)
            total_energy_metrics_paragraph = f"""
            <b>Mittlere Leistungsaufnahme:</b> {mean_power:.2f} W<br/>
            <b>Maximale Leistung:</b> {peak_power:.2f} W<br/>
            <b>Minimale Leistung:</b> {min_power:.2f} W<br/>
            <b>Energieverbrauch pro Betriebsstunde:</b> {total_energy:.2f} kWh<br/>
            """
            total_energy_metrics = Paragraph(total_energy_metrics_paragraph, styles['NormalStyle'])
            table_data.append([total_energy_chart, total_energy_metrics])

            # Add the table to the elements
            table = Table(table_data, colWidths=[4.5 * inch, 2.5 * inch])
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

            # Add pie chart for energy distribution
            total_average_energy = df[total_energy_column].mean()
            pie_sizes = [size / total_average_energy * 100 for size in pie_sizes]

            pie_chart, pie_legend_paragraph = add_pie_chart_to_pdf(pie_labels, pie_sizes, f"{state} - Anteil der Komponenten an der Gesamtenergie")

            # Add the pie chart and its legend to the table
            pie_table_data = [[pie_chart, pie_legend_paragraph]]
            pie_table = Table(pie_table_data, colWidths=[4.5 * inch, 2.5 * inch])
            pie_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
            ]))
            elements.append(pie_table)
            elements.append(Spacer(1, 12))

            # Add metrics to comparison table
            comparison_data.append([state, f"{mean_power:.2f}", f"{peak_power:.2f}", f"{min_power:.2f}", f"{total_energy:.2f}"])

            # Add forecast data
            annual_energy_consumption = total_energy * hours_per_year * operating_time_percentage[state]
            forecast_data.append([state, f"{operating_time_percentage[state] * 100:.2f}%", f"{annual_energy_consumption:.2f} kWh"])

    # Add comparison table to the PDF
    elements.append(Paragraph("<b>Vergleich der Kenngrößen der Gesamtenergie für alle Zustände</b>", styles['SubtitleStyle']))
    comparison_table = Table(comparison_data, colWidths=[0.75 * inch] + [1.5 * inch] * 3 + [1.75 * inch])
    comparison_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
    ]))
    elements.append(comparison_table)
    elements.append(Spacer(1, 12))

    # Add forecast table to the PDF
    elements.append(Paragraph("<b>Jahresprognose des Energieverbrauchs</b>", styles['SubtitleStyle']))
    forecast_table = Table(forecast_data, colWidths=[2 * inch, 2.5 * inch, 2.5 * inch])
    forecast_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
    ]))
    elements.append(forecast_table)
    elements.append(Spacer(1, 12))

    # Add explanation for forecast calculation
    forecast_explanation = f"""
    <b>Hinweis:</b> Die Jahresprognose basiert auf einer prozentualen Aufteilung der Betriebszeit: 
    Stand-By ({operating_time_percentage['Stand-By'] * 100:.2f}%), Ready ({operating_time_percentage['Ready'] * 100:.2f}%) und Prozess ({operating_time_percentage['Prozess'] * 100:.2f}%). 
    Der jährliche Energieverbrauch wurde berechnet, indem der stündliche Energieverbrauch (in kWh) 
    mit der Anzahl der Stunden pro Jahr (230 Tage x 8 Stunden) und dem Prozentsatz der Betriebszeit multipliziert wurde.
    """
    elements.append(Paragraph(forecast_explanation, styles['NormalStyle']))

    # Build the PDF
    doc.build(elements)

# Example usage
if __name__ == '__main__':
    machine_info = {
        'company': 'Beispielunternehmen',
        'model': 'Modell XYZ',
        'location': 'Hannover',
        'date': '2024-07-01',
        'time': '09:00'
    }

    # Load example CSV data
    standby_data = pd.read_csv('uploaded_file_standby.csv')
    ready_data = pd.read_csv('uploaded_file_ready.csv')
    process_data = pd.read_csv('uploaded_file_process.csv')

    # Example percentages
    percentages = {'standby': 15, 'ready': 5, 'process': 40}

    # Generate PDF
    create_energy_audit_pdf(machine_info, standby_data, ready_data, process_data, percentages, 'energieeinsparungsaudit.pdf')
