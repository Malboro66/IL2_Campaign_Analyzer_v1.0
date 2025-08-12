import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class IL2PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Configura estilos customizados para o PDF"""
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))

        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))

        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))

    def generate_pilot_report(self, processed_data, output_path):
        """Gera relatório completo do piloto em PDF"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # Título principal
        title = Paragraph("IL-2 Sturmovik - Relatório de Campanha", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 20))

        # Data de geração
        generation_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        date_para = Paragraph(f"Relatório gerado em: {generation_date}", self.styles['CustomNormal'])
        story.append(date_para)
        story.append(Spacer(1, 30))

        # Seção Pilot Profile
        self.add_pilot_profile_section(story, processed_data['pilot'])

        # Seção Squad
        self.add_squad_section(story, processed_data['squad'])

        # Seção Aces
        self.add_aces_section(story, processed_data['aces'])

        # Seção Missions
        self.add_missions_section(story, processed_data['missions'])

        # Construir PDF
        doc.build(story)
        return True

    def add_pilot_profile_section(self, story, pilot_data):
        """Adiciona seção do perfil do piloto"""
        story.append(Paragraph("Perfil do Piloto", self.styles['CustomHeading']))

        # Informações básicas
        basic_info = [
            ["Nome:", pilot_data.get('name', 'N/A')],
            ["Número Serial:", str(pilot_data.get('serial_number', 'N/A'))],
            ["Esquadrão:", pilot_data.get('squadron', 'N/A')],
            ["Data da Campanha:", pilot_data.get('campaign_date', 'N/A')],
            ["Total de Missões:", str(pilot_data.get('total_missions', 0))]
        ]

        # Informações complementares se disponíveis
        if pilot_data.get('birth_date'):
            basic_info.append(["Data de Nascimento:", pilot_data['birth_date']])
        
        if pilot_data.get('birth_place'):
            basic_info.append(["Local de Nascimento:", pilot_data['birth_place']])
        
        if pilot_data.get('age'):
            basic_info.append(["Idade:", str(pilot_data['age']) + " anos"])

        # Criar tabela
        table = Table(basic_info, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)

        # Tipos de aeronaves
        if pilot_data.get('aircraft_types'):
            story.append(Spacer(1, 15))
            aircraft_para = Paragraph(
                f"<b>Aeronaves Pilotadas:</b> {', '.join(pilot_data['aircraft_types'])}", 
                self.styles['CustomNormal']
            )
            story.append(aircraft_para)

        story.append(Spacer(1, 20))

    def add_squad_section(self, story, squad_data):
        """Adiciona seção do esquadrão"""
        story.append(Paragraph("Informações do Esquadrão", self.styles['CustomHeading']))

        squad_info = [
            ["Nome do Esquadrão:", squad_data.get('name', 'N/A')],
            ["Total de Vitórias:", str(squad_data.get('total_victories', 0))],
            ["Membros Conhecidos:", str(len(squad_data.get('members', [])))]
        ]

        table = Table(squad_info, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)

        # Atividades recentes
        if squad_data.get('recent_activities'):
            story.append(Spacer(1, 15))
            story.append(Paragraph("Atividades Recentes:", self.styles['CustomNormal']))
            
            for activity in squad_data['recent_activities'][:5]:  # Mostrar apenas as 5 mais recentes
                activity_text = f"• {activity.get('date', 'N/A')}: {activity.get('activity', 'N/A')}"
                story.append(Paragraph(activity_text, self.styles['CustomNormal']))

        story.append(Spacer(1, 20))

    def add_aces_section(self, story, aces_data):
        """Adiciona seção dos ases"""
        story.append(Paragraph("Lista de Ases", self.styles['CustomHeading']))

        if not aces_data:
            story.append(Paragraph("Nenhum ás encontrado.", self.styles['CustomNormal']))
            story.append(Spacer(1, 20))
            return

        # Cabeçalho da tabela
        aces_table_data = [["Posição", "Nome", "Esquadrão", "Vitórias"]]

        # Dados dos ases (top 10)
        for i, ace in enumerate(aces_data[:10], 1):
            aces_table_data.append([
                str(i),
                ace.get('name', 'N/A'),
                ace.get('squadron', 'N/A'),
                str(ace.get('victories', 0))
            ])

        table = Table(aces_table_data, colWidths=[0.8*inch, 2.2*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
        story.append(Spacer(1, 20))

    def add_missions_section(self, story, missions_data):
        """Adiciona seção das missões"""
        story.append(Paragraph("Histórico de Missões", self.styles['CustomHeading']))

        if not missions_data:
            story.append(Paragraph("Nenhuma missão encontrada.", self.styles['CustomNormal']))
            return

        # Resumo das missões
        total_missions = len(missions_data)
        story.append(Paragraph(f"Total de Missões: {total_missions}", self.styles['CustomNormal']))
        story.append(Spacer(1, 10))

        # Tabela das missões (últimas 15)
        missions_table_data = [["Data", "Aeronave", "Missão", "Local", "Altitude"]]

        for mission in missions_data[:15]:  # Mostrar apenas as 15 mais recentes
            missions_table_data.append([
                mission.get('date', 'N/A'),
                mission.get('aircraft', 'N/A'),
                mission.get('duty', 'N/A'),
                mission.get('locality', 'N/A'),
                mission.get('altitude', 'N/A')
            ])

        table = Table(missions_table_data, colWidths=[1*inch, 1.2*inch, 1.5*inch, 1.3*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)

        # Detalhes de missões selecionadas
        if len(missions_data) > 0:
            story.append(PageBreak())
            story.append(Paragraph("Detalhes das Missões Recentes", self.styles['CustomHeading']))

            for i, mission in enumerate(missions_data[:5]):  # Detalhar apenas as 5 mais recentes
                story.append(Paragraph(f"Missão {i+1} - {mission.get('date', 'N/A')}", self.styles['CustomNormal']))
                
                mission_details = [
                    ["Data:", mission.get('date', 'N/A')],
                    ["Hora:", mission.get('time', 'N/A')],
                    ["Aeronave:", mission.get('aircraft', 'N/A')],
                    ["Tipo de Missão:", mission.get('duty', 'N/A')],
                    ["Local:", mission.get('locality', 'N/A')],
                    ["Altitude:", mission.get('altitude', 'N/A')],
                    ["Esquadrão:", mission.get('squadron', 'N/A')]
                ]

                detail_table = Table(mission_details, colWidths=[1.5*inch, 3.5*inch])
                detail_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                story.append(detail_table)

                # Relatório da missão
                if mission.get('report') and mission['report'] != 'N/A':
                    story.append(Spacer(1, 10))
                    story.append(Paragraph("Relatório:", self.styles['CustomNormal']))
                    report_text = mission['report'].replace('\n', '<br/>')
                    story.append(Paragraph(report_text, self.styles['CustomNormal']))

                story.append(Spacer(1, 15))

    def generate_quick_summary(self, processed_data, output_path):
        """Gera um resumo rápido em PDF"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # Título
        title = Paragraph("IL-2 Sturmovik - Resumo da Campanha", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 30))

        pilot_data = processed_data['pilot']

        # Informações principais
        summary_data = [
            ["Piloto:", pilot_data.get('name', 'N/A')],
            ["Esquadrão:", pilot_data.get('squadron', 'N/A')],
            ["Total de Missões:", str(pilot_data.get('total_missions', 0))],
            ["Data da Campanha:", pilot_data.get('campaign_date', 'N/A')]
        ]

        table = Table(summary_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)

        # Top 5 Ases
        story.append(Spacer(1, 30))
        story.append(Paragraph("Top 5 Ases", self.styles['CustomHeading']))

        aces_data = processed_data['aces'][:5]
        if aces_data:
            aces_table_data = [["Nome", "Esquadrão", "Vitórias"]]
            for ace in aces_data:
                aces_table_data.append([
                    ace.get('name', 'N/A'),
                    ace.get('squadron', 'N/A'),
                    str(ace.get('victories', 0))
                ])

            aces_table = Table(aces_table_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            aces_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(aces_table)

        doc.build(story)
        return True

