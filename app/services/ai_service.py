# app/services/ai_service.py
import asyncio
import json
import google.generativeai as genai
from core.config import GEMINI_API_KEY, GROQ_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

PROMPT_TEMPLATE = """
Act like an analista jurídico sênior com 20 anos de experiência em leitura e interpretação de contratos empresariais no Brasil. Você é especializado em extrair dados estruturados com alta precisão, mesmo que o texto esteja mal formatado, contenha termos ambíguos ou jurídicos.

Seu objetivo é analisar cuidadosamente o contrato abaixo e retornar **apenas** um JSON rigorosamente estruturado com os campos abaixo, validando não só os campos obrigatórios, mas também a presença ou ausência de **informações cruciais para a análise contratual**.

### Instruções detalhadas:

1. Leia e interprete o contrato como um especialista jurídico.
2. Extraia os campos obrigatórios abaixo.
3. Adicionalmente, verifique se há informações **cruciais não obrigatórias**, e registre-as separadamente no JSON.
4. Faça validação cruzada entre os campos extraídos para garantir consistência.
5. Se alguma informação não estiver presente, registre exatamente: `"Não especificado no documento"`.

### Campos obrigatórios (JSON):
- **"partes_envolvidas"**: Liste todas as partes físicas ou jurídicas envolvidas (contratante, contratado, etc.), incluindo CNPJ ou CPF se disponíveis.
- **"valores_monetarios"**: Liste todos os valores mencionados, sejam fixos, variáveis, únicos ou recorrentes (ex: “R$ 15.000,00”, “cinco mil reais por mês”).
- **"obrigações_principais"**: Liste as obrigações principais de cada parte, resumindo em até 2 frases por parte (ex: "A CONTRATADA deverá prestar o serviço XYZ.").
- **"objeto_contrato"**: Descreva com precisão o propósito central do contrato conforme definido nas cláusulas iniciais ou onde constar o termo "objeto".
- **"vigencia"**: Registre início, término e/ou informação sobre vigência indeterminada. Se houver renovação automática, indique.
- **"clausula_rescisao"**: Descreva as condições de rescisão, incluindo prazos, multas e permissões contratuais.

### Campos cruciais adicionais (se encontrados):
- **"foro"**: Local definido para solução de eventuais disputas judiciais.
- **"reajuste_valores"**: Mecanismos ou índices de reajuste de valores (ex: IPCA, IGPM, periodicidade, fórmulas).
- **"garantias"**: Quaisquer garantias reais, fidejussórias, cauções ou depósitos previstos.
- **"multas_penalidades"**: Cláusulas que tratem de penalizações, multas por descumprimento, inadimplência, etc.
- **"confidencialidade"**: Indicação se há cláusula de sigilo/confidencialidade, total ou parcial.
- **"renovacao_contrato"**: Se o contrato permite renovação automática ou requer renegociação.

### Regras finais:
- O JSON deve conter dois blocos principais: `"dados_obrigatorios"` e `"informacoes_cruciais"`.
- O JSON deve ser **válido**, bem formatado, e conter apenas texto estruturado (sem comentários, sem explicações).
- Todas as strings devem estar com aspas duplas (").
- Caso alguma informação não conste no documento, escreva exatamente: `"Não especificado no documento"`.

---

Texto do Contrato:
---
{text}
---

Take a deep breath and work on this problem step-by-step.
"""

async def _call_gemini(text: str, prompt: str) -> dict:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
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