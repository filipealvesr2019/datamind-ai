"""Gerador de Relatório Executivo em PDF — DataMind AI
Constrói relatórios corporativos em A4 com cabeçalho, pergunta do gestor,
resumo executivo formatado, gráfico Plotly (PNG) e tabela de dados.
"""

import base64
import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


COR_PRIMARIA = colors.HexColor("#4f46e5")      # Índigo DataMind
COR_ESCURA = colors.HexColor("#0f172a")        # Slate 900
COR_TEXTO = colors.HexColor("#334155")         # Slate 700
COR_SUAVE = colors.HexColor("#64748b")         # Slate 500
COR_FUNDO_CLARO = colors.HexColor("#f8fafc")   # Slate 50
COR_BORDA = colors.HexColor("#e2e8f0")         # Slate 200


def _formatar_inline_markdown(texto: str) -> str:
    """Converte negrito/itálico Markdown em tags seguras para ReportLab Paragraph."""
    seguro = escape(texto)
    seguro = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", seguro)
    seguro = re.sub(r"\*(.+?)\*", r"<i>\1</i>", seguro)
    seguro = re.sub(r"`(.+?)`", r"<font face='Courier'>\1</font>", seguro)
    return seguro


def _desenhar_rodape(canvas, doc):
    """Desenha rodapé institucional com numeração de página."""
    canvas.saveState()
    canvas.setStrokeColor(COR_BORDA)
    canvas.setLineWidth(0.5)
    canvas.line(1.8 * cm, 1.5 * cm, A4[0] - 1.8 * cm, 1.5 * cm)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(COR_SUAVE)
    canvas.drawString(1.8 * cm, 1.05 * cm, "DataMind AI — Analista Empresarial Inteligente")
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.05 * cm, f"Página {doc.page}")
    canvas.restoreState()


def _converter_markdown_em_flowables(
    resposta_md: str,
    styles: Dict[str, ParagraphStyle],
    ignorar_tabelas_md: bool = False
) -> List[Any]:
    """Converte texto Markdown da resposta da IA em blocos ReportLab."""
    flowables: List[Any] = []
    if not resposta_md:
        return flowables

    for linha_bruta in resposta_md.splitlines():
        linha = linha_bruta.strip()
        if not linha:
            flowables.append(Spacer(1, 4))
            continue

        # Se já vamos renderizar a tabela estruturada de dados_tabela, pula tabelas Markdown duplicadas
        if ignorar_tabelas_md and linha.startswith("|") and linha.endswith("|"):
            continue
        if re.match(r"^\|?[\s:\-|]+\|?$", linha):
            continue

        if linha.startswith("### "):
            flowables.append(Paragraph(_formatar_inline_markdown(linha[4:]), styles["h3"]))
        elif linha.startswith("## "):
            flowables.append(Paragraph(_formatar_inline_markdown(linha[3:]), styles["h2"]))
        elif linha.startswith("# "):
            flowables.append(Paragraph(_formatar_inline_markdown(linha[2:]), styles["h2"]))
        elif linha.startswith(("- ", "* ", "• ")):
            texto_item = _formatar_inline_markdown(linha[2:])
            flowables.append(Paragraph(f"• {texto_item}", styles["bullet"]))
        else:
            flowables.append(Paragraph(_formatar_inline_markdown(linha), styles["body"]))

    return flowables


def gerar_relatorio_pdf(
    pergunta: str,
    resposta: str,
    dados_tabela: Optional[List[Dict[str, Any]]] = None,
    grafico_imagem_base64: Optional[str] = None,
    titulo_relatorio: str = "Relatório Executivo — DataMind AI"
) -> bytes:
    """Gera e retorna os bytes de um arquivo PDF executivo formatado."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2.2 * cm,
        title=titulo_relatorio,
        author="DataMind AI"
    )

    base = getSampleStyleSheet()
    styles = {
        "brand": ParagraphStyle(
            "Brand",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.white,
            leading=20,
            spaceAfter=2,
        ),
        "brand_sub": ParagraphStyle(
            "BrandSub",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            textColor=colors.HexColor("#c7d2fe"),
            leading=11,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=COR_PRIMARIA,
            spaceBefore=10,
            spaceAfter=5,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            textColor=COR_ESCURA,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=COR_ESCURA,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=COR_TEXTO,
            leading=14,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=COR_TEXTO,
            leading=14,
            leftIndent=12,
            spaceAfter=3,
        ),
        "pergunta": ParagraphStyle(
            "Pergunta",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=COR_ESCURA,
            leading=14,
        ),
        "cell_header": ParagraphStyle(
            "CellHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white,
            leading=10,
        ),
        "cell": ParagraphStyle(
            "Cell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=COR_TEXTO,
            leading=10,
        ),
    }

    largura_util = A4[0] - 3.6 * cm
    elementos: List[Any] = []

    # 1. Cabeçalho Corporativo
    agora_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
    header_table = Table(
        [[
            Paragraph("DataMind AI", styles["brand"]),
            Paragraph(f"Relatório Executivo<br/>Gerado em {agora_str}", styles["brand_sub"]),
        ]],
        colWidths=[largura_util * 0.6, largura_util * 0.4],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_ESCURA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elementos.append(header_table)
    elementos.append(Spacer(1, 12))

    # 2. Pergunta do Gestor
    if pergunta:
        pergunta_box = Table(
            [[Paragraph(f"Solicitação: {escape(pergunta)}", styles["pergunta"])]],
            colWidths=[largura_util],
        )
        pergunta_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COR_FUNDO_CLARO),
            ("BOX", (0, 0), (-1, -1), 0.75, COR_BORDA),
            ("LINEBEFORE", (0, 0), (0, -1), 3, COR_PRIMARIA),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elementos.append(pergunta_box)
        elementos.append(Spacer(1, 10))

    # 3. Análise Executiva
    elementos.append(Paragraph("ANÁLISE EXECUTIVA", styles["section"]))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COR_BORDA, spaceAfter=6))

    tem_dados_tabela = bool(dados_tabela and len(dados_tabela) > 0)
    elementos.extend(_converter_markdown_em_flowables(
        resposta,
        styles,
        ignorar_tabelas_md=tem_dados_tabela
    ))
    elementos.append(Spacer(1, 8))

    # 4. Gráfico Plotly (se enviado em base64)
    if grafico_imagem_base64:
        try:
            b64_limpo = grafico_imagem_base64
            if "," in b64_limpo:
                b64_limpo = b64_limpo.split(",", 1)[1]
            img_bytes = base64.b64decode(b64_limpo)
            with PILImage.open(io.BytesIO(img_bytes)) as pil_img:
                w_px, h_px = pil_img.size

            aspect = h_px / float(w_px) if w_px else 0.55
            img_w = largura_util
            img_h = min(img_w * aspect, 10.5 * cm)
            if img_h == 10.5 * cm and aspect > 0:
                img_w = img_h / aspect

            elementos.append(Paragraph("VISUALIZAÇÃO GRÁFICA", styles["section"]))
            elementos.append(HRFlowable(width="100%", thickness=0.5, color=COR_BORDA, spaceAfter=6))
            elementos.append(Image(io.BytesIO(img_bytes), width=img_w, height=img_h))
            elementos.append(Spacer(1, 10))
        except Exception:
            # Se a imagem vier corrompida, segue gerando o PDF sem falhar
            pass

    # 5. Tabela de Dados Estruturados
    if tem_dados_tabela:
        elementos.append(Paragraph("DADOS DETALHADOS", styles["section"]))
        elementos.append(HRFlowable(width="100%", thickness=0.5, color=COR_BORDA, spaceAfter=6))

        colunas = list(dados_tabela[0].keys())
        num_cols = max(len(colunas), 1)
        col_widths = [largura_util / num_cols] * num_cols

        linhas_tabela = [
            [Paragraph(escape(str(col).replace("_", " ").upper()), styles["cell_header"]) for col in colunas]
        ]

        for row in dados_tabela[:50]:
            linha = []
            for col in colunas:
                val = row.get(col, "")
                if isinstance(val, float):
                    val_str = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                else:
                    val_str = str(val if val is not None else "-")
                linha.append(Paragraph(escape(val_str), styles["cell"]))
            linhas_tabela.append(linha)

        tabela_pdf = Table(linhas_tabela, colWidths=col_widths, repeatRows=1)
        tabela_pdf.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_FUNDO_CLARO]),
            ("GRID", (0, 0), (-1, -1), 0.4, COR_BORDA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabela_pdf)

    doc.build(elementos, onFirstPage=_desenhar_rodape, onLaterPages=_desenhar_rodape)
    return buffer.getvalue()
