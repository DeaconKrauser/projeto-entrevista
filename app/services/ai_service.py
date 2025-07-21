# app/services/ai_service.py
import asyncio
import json
import google.generativeai as genai
from core.config import GEMINI_API_KEY, GROQ_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

PROMPT_TEMPLATE = """
Aja como um analista jurídico sênior, com mais de 20 anos de experiência em leitura, interpretação e extração de dados de contratos empresariais celebrados no Brasil. Você é especialista em identificar e organizar informações relevantes mesmo em documentos mal formatados, com uso excessivo de jargões legais, ambiguidade ou omissões.

Seu objetivo é analisar cuidadosamente o contrato abaixo e retornar **apenas** um JSON bem estruturado, contendo dois blocos principais: `"dados_obrigatorios"` e `"informacoes_cruciais"`. Cada campo deve refletir fielmente as informações extraídas do contrato. Caso algum dado esteja ausente, registre exatamente: `"Não especificado no documento"`.

### Etapas da tarefa:

1. Leia o contrato como um profissional jurídico experiente.
2. Extraia os **dados obrigatórios** listados abaixo.
3. Verifique e registre também **informações cruciais adicionais**, se estiverem presentes.
4. Valide a consistência entre os dados extraídos.
5. Retorne um JSON **válido**, formatado corretamente, sem comentários ou explicações extras.

### Bloco: dados_obrigatorios
- **"partes_envolvidas"**: Todas as pessoas físicas ou jurídicas mencionadas (ex: contratante, contratado), com CNPJ ou CPF, se disponíveis.
- **"valores_monetarios"**: Todos os valores citados no contrato, sejam fixos, variáveis, únicos ou recorrentes (ex: "R$ 15.000,00", "cinco mil reais por mês").
- **"obrigações_principais"**: Resumo das obrigações de cada parte (máximo 2 frases por parte).
- **"objeto_contrato"**: Descrição clara do objetivo principal do contrato.
- **"vigencia"**: Informar datas de início e fim da vigência, se é indeterminada, e se há renovação automática.
- **"clausula_rescisao"**: Condições para rescisão, incluindo prazos, multas e permissões.

### Bloco: informacoes_cruciais
(Incluir apenas se as informações forem encontradas no contrato)
- **"foro"**: Local definido para resolução de disputas judiciais.
- **"reajuste_valores"**: Índices ou condições de reajuste (ex: IPCA, IGP-M, periodicidade, fórmulas).
- **"garantias"**: Cauções, depósitos, garantias reais ou pessoais.
- **"multas_penalidades"**: Penalidades aplicáveis por inadimplência ou descumprimento contratual.
- **"confidencialidade"**: Existência de cláusula de sigilo/confidencialidade.
- **"renovacao_contrato"**: Informação sobre renovação automática ou necessidade de renegociação.

### Regras finais:
- O JSON deve conter **somente** os dois blocos especificados.
- Todas as strings devem estar entre **aspas duplas** (`"`).
- Se uma informação não estiver presente no contrato, registre exatamente: `"Não especificado no documento"`.

---

Texto do contrato a ser analisado:
---
{text}
---
"""


async def _call_gemini(text: str, prompt: str) -> dict:
    model = genai.GenerativeModel('gemini-2.0-flash')
    try:
        full_prompt = prompt.format(text=text)
        response = await model.generate_content_async(full_prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        return {"error": "Falha ao analisar a resposta da IA", "details": str(e)}

async def _call_groq(text: str, prompt: str) -> dict:
    print("SIMULANDO CHAMADA PARA A API GROQ")
    await asyncio.sleep(1) # Demora reduzida para 1 segundo
    return {
        "partes_envolvidas": ["Simulado via Groq: Empresa X (CNPJ: 12.345.678/0001-99)", "Simulado via Groq: Fornecedor Y"],
        "valores_monetarios": ["R$ 5.000,00 (simulado)"],
        "obrigações_principais": "Fornecedor Y deve entregar o produto X até a data Z (simulado).",
        "objeto_contrato": "Compra e venda de produto X (simulado).",
        "vigencia": "12 meses a partir de 01/01/2025 (simulado).",
        "clausula_rescisao": "Multa de 20% sobre o valor do contrato (simulado)."
    }

async def extract_contract_data(text: str, provider: str) -> dict:
    if provider == 'gemini':
        return await _call_gemini(text, PROMPT_TEMPLATE)
    elif provider == 'groq':
        return await _call_groq(text, PROMPT_TEMPLATE)
    else:
        raise ValueError(f"Provedor de IA desconhecido: {provider}")