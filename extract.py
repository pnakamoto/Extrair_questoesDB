import PyPDF2
import re
import json

# Caminho do arquivo PDF e do JSON de saída
pdf_path = "BANCO DE QUESTÕES R1.pdf"
json_path = "questoes_completas.json"

def extrair_texto_pdf(pdf_path):
    texto = ""
    with open(pdf_path, "rb") as file:
        leitor = PyPDF2.PdfReader(file)
        for pagina in leitor.pages:
            page_text = pagina.extract_text()
            if page_text:
                texto += page_text + "\n"
    return texto

def extrair_questoes_e_gabarito(texto):
    # Dividir o texto em duas partes: (1) as questões e (2) o gabarito
    partes = re.split(r"GABARITO\s+LIBERADO\s+PELA\s+BANCA:", texto, flags=re.IGNORECASE)
    if len(partes) < 2:
        print("Não foi possível encontrar a seção do gabarito.")
        return [], ""
    questoes_texto = partes[0]
    gabarito_texto = partes[1]

    # Remover cabeçalhos e rodapés indesejados (se houver)
    questoes_texto = questoes_texto.strip()
    gabarito_texto = gabarito_texto.strip()

    # Expressão regular para extrair cada questão (supondo que cada questão inicie com "número)" )
    # Usamos DOTALL para que o . corresponda a quebras de linha.
    padrao_questao = re.compile(r"(\d+)\)\s*(.+?)(?=\n\d+\)|\n\d+\.\s|$)", re.DOTALL)
    questoes_brutas = padrao_questao.findall(questoes_texto)

    questoes = []
    for num_str, conteudo in questoes_brutas:
        numero = int(num_str)
        # Separa a primeira linha (pergunta) e as seguintes (alternativas)
        linhas = [linha.strip() for linha in conteudo.strip().split("\n") if linha.strip()]
        if not linhas:
            continue
        pergunta = linhas[0]
        alternativas = []
        # Usamos uma regex para capturar alternativas com padrão "Letra) texto"
        padrao_alternativa = re.compile(r"([A-E])\)\s*(.+)")
        for linha in linhas[1:]:
            match = padrao_alternativa.match(linha)
            if match:
                letra, alt_text = match.groups()
                alternativas.append(alt_text.strip())
        # Consideramos apenas questões com exatamente 5 alternativas
        if len(alternativas) == 5:
            questoes.append({
                "number": numero,
                "question": pergunta,
                "options": alternativas
            })
    # Processar o gabarito: remover tudo que não for letra A-E e juntar
    letras = re.findall(r"[A-E]", gabarito_texto.upper())
    # Supondo que as primeiras 75 letras correspondam às respostas das 75 questões
    gabarito = letras[:75]
    return questoes, gabarito

def juntar_questoes_com_gabarito(questoes, gabarito):
    # Mapeia letra para índice (A->0, B->1, ...)
    mapa = {"A":0, "B":1, "C":2, "D":3, "E":4}
    questoes_completas = []
    for q in questoes:
        num = q.get("number")
        if num <= len(gabarito):
            letra = gabarito[num - 1]  # assumindo que a questão número 1 corresponde à posição 0
            if letra in mapa:
                q["answer"] = mapa[letra]
                questoes_completas.append(q)
    return questoes_completas

def main():
    texto = extrair_texto_pdf(pdf_path)
    questoes, gabarito = extrair_questoes_e_gabarito(texto)
    print(f"Foram encontradas {len(questoes)} questões e {len(gabarito)} respostas no gabarito.")
    questoes_completas = juntar_questoes_com_gabarito(questoes, gabarito)
    print(f"Foram processadas {len(questoes_completas)} questões completas.")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questoes_completas, f, indent=4, ensure_ascii=False)
    print(f"Arquivo JSON gerado em: {json_path}")

if __name__ == "__main__":
    main()
