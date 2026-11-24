# Etapa final — Dashboard Streamlit / Plotly com PostgreSQL Aiven

## 1. Status e escopo

- **Código entregue** neste repositório: `dashboard/app.py`, `dashboard/db.py`, `dashboard/analytics.py`.
- **Banco existente:** Aiven PostgreSQL, `observatorio`, tabela `lattes_analytics.perfil_pesquisadores_lattes_2023`.
- **Camada de dashboard:** consultas SQL agregadas e parametrizadas; não lê arquivos CSV locais.
- **Publicação e acesso ao banco remoto:** **pendentes de configuração e validação**. Não confundir a presença do código com um aplicativo já publicado.
- **Origem dos dados:** CNPq Painel Lattes, ano de referência 2023, extração com `PQ 1A = Não`.

## 2. Rodar localmente (Windows PowerShell)

Na raiz do clone do repositório:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edite apenas seu .env LOCAL; não o envie ao GitHub
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

O arquivo `.env` deve conter `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` e `DB_SSLMODE`. Para PostgreSQL Aiven, `DB_PORT` deve refletir a porta do console Aiven; 17025 é o valor previamente documentado neste projeto e precisa ser confirmado antes da conexão. `.env` é ignorado pelo Git.

**Nunca publique `.env`, prints de senha, tokens ou URLs completas com credenciais.**

O banco deve ter a tabela física existente e os registros carregados, conforme `docs/reproducao_fase2.md`. Não há motivo para executar Terraform apply ou repetir a carga apenas para iniciar o dashboard.

## 3. Usuário de somente leitura recomendado

Em vez de usar `avnadmin` em um aplicativo público, solicite ao administrador do banco um usuário dedicado que tenha somente `SELECT` na tabela analítica. Exemplo a ser adaptado e executado **somente por alguém autorizado**:

```sql
-- Exemplo de política de privilégios (não executar sem aprovação)
CREATE ROLE observatorio_visualizacao LOGIN PASSWORD '<definir_em_canal_seguro>';
GRANT CONNECT ON DATABASE observatorio TO observatorio_visualizacao;
GRANT USAGE ON SCHEMA lattes_analytics TO observatorio_visualizacao;
GRANT SELECT ON TABLE lattes_analytics.perfil_pesquisadores_lattes_2023 TO observatorio_visualizacao;
```

O código da aplicação também solicita conexão PostgreSQL em modo de leitura através de `default_transaction_read_only=on`. **Isso é uma defesa adicional, não substitui as permissões SQL.**

Use TLS: `DB_SSLMODE=require` criptografa a conexão; para verificar também a CA e identidade do servidor, prefira `DB_SSLMODE=verify-full` com `DB_SSLROOTCERT` apontando para CA válida, quando disponível. Não desative TLS.

## 4. Hospedagem no Streamlit Community Cloud

1. Atualize o repositório GitHub com os arquivos da etapa final. Confira alterações por Pull Request antes do merge.
2. Acesse a plataforma de hospedagem do Streamlit, vincule o GitHub e selecione o repositório e a branch que contém o código.
3. Informe **`dashboard/app.py`** como entrypoint e selecione as dependências do repositório (`requirements.txt`).
4. Na configuração privada **Secrets** da aplicação, cole o conteúdo do exemplo `.streamlit/secrets.toml.example`, substituindo os placeholders pelo usuário de banco **somente leitura**.
5. Verifique os controles de acesso / redes permitidas na Aiven. O serviço precisa aceitar conexões originadas da hospedagem, mas **não abra a rede indiscriminadamente sem avaliar os riscos e alternativas**. O Streamlit Community Cloud pode não oferecer IP de saída fixo; nesse caso considere solução de rede/hospedagem com origem controlável.
6. Publique a aplicação **somente após** aprovar segurança, privacidade das consultas e disponibilidade do banco. Não versionar `secrets.toml`.
7. Verifique o dashboard com os filtros em tempo real; compare os números de referência com os resultados SQL na Aiven.

Exemplo genérico de Secrets, **sem credenciais reais**:

```toml
[connections.postgresql]
host = "host-fornecido-pela-aiven"
port = 17025
database = "observatorio"
username = "usuario_somente_leitura"
password = "CONFIGURAR_SOMENTE_EM_SECRETS"
sslmode = "require"
```

A aplicação aceita igualmente variáveis `DB_*` locais. O arquivo `.streamlit/secrets.toml.example` é apenas um modelo; o arquivo verdadeiro `.streamlit/secrets.toml` é ignorado pelo Git.

> O banco permanece na Aiven. A implantação do Streamlit Cloud é realizada pelo painel da plataforma, sem necessidade de novo recurso Terraform na configuração presente. Documentar o provedor de hospedagem e suas configurações. Se houver provisionamento adicional automatizável, adicionar e versionar os scripts correspondentes antes da entrega final.

## 5. Como conferir que os dados realmente vêm do banco

No painel, aplique um filtro de Região ou Sexo e observe a mudança nos totais e indicadores. A aplicação executa `GROUP BY` no PostgreSQL e usa o valor `SUM(quantidade)`; ela não carrega CSV em tempo de execução.

Consultas de referência **somente leitura** na Aiven:

```sql
SELECT COUNT(*) AS linhas, SUM(quantidade) AS pessoas
FROM lattes_analytics.perfil_pesquisadores_lattes_2023;
-- Esperado da validação de novembro/2026: 25820 linhas, 26009 ponderados

SELECT sexo, SUM(quantidade) AS pessoas
FROM lattes_analytics.perfil_pesquisadores_lattes_2023
GROUP BY sexo ORDER BY pessoas DESC;
```

A aplicação faz cache dos agregados por até **60 segundos**, para evitar consultas desnecessárias. O botão **Atualizar consultas** elimina o cache para nova consulta. Isso é consulta direta à fonte relacional, **não streaming nem atualização de registros em tempo real**; o próprio recorte do CNPq é fixo em 2023.

## 6. Quatro KPIs e denominadores

| KPI | Numerador | Denominador | Observação |
|---|---|---|---|
| Participação feminina | `SUM(quantidade)` para `sexo='Feminino'` | Todos com sexo conhecido | Exclui `Não informado`; mostra cobertura |
| Participação preta ou parda | Soma para raça/cor `Preta` e `Parda` | Todos com raça/cor conhecida | Não equipara autodeclaração à população nacional; mostra cobertura |
| Mulheres pretas ou pardas | Soma para `sexo='Feminino'` e raça/cor `Preta`/`Parda` | Todos com **ambos** conhecidos | Interseção de atributos; não representa aprovação de bolsas |
| Presença de bolsa PQ | Soma ponderada para `bolsista_pq='Sim'` | Todos no recorte | Presença/histórico no cadastro; **não** taxa de aprovação |

As tabelas e gráficos usam apenas consultas agregadas. Gráficos disponíveis: distribuição por sexo, raça/cor, mapa de calor interseccional, taxa PQ por sexo, região de atuação e grande área. Filtros: Região, UF, grande área, nível de formação, sexo e raça/cor. Por prudência, o aplicativo limita a dois filtros simultâneos, mas esse limite **não neutraliza ataques por consultas diferenciais**.

## 7. Segurança, privacidade e limites da interpretação

- Os resultados de células de **1 a 4 pessoas** são suprimidos. Para reduzir recuperação por subtração, a distribuição inteira é ocultada quando contém uma célula pequena.
- Este é um **mecanismo mínimo**, não uma proteção formal para publicação irrestrita: diferenças entre filtros e totais de categorias podem revelar resultados pequenos. A equipe precisa avaliar consultas complementares, categorias, ataques por diferença, controles de acesso e eventual preagregação pública antes de habilitar acesso aberto. **Não publique indiscriminadamente enquanto essa revisão não estiver concluída.**
- Não há exportação de linhas, nem download da tabela, nem endpoint SQL genérico.
- A base contém células agregadas (não perfis individuais), mas análises interseccionais raras merecem precaução.
- Não há propostas submetidas/rejeitadas e a extração exclui PQ 1A; **não é possível medir aprovação, concessão, discriminação ou causalidade** com esses dados.
- Este é um recorte único **2023**; não usar gráfico ou filtro temporal plurianual.
- A ausência de informações demográficas deve constar na interpretação de cada KPI.

## 8. Testes e verificação

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m "not integracao"
```

Novos testes `tests/test_dashboard.py` usam **SQLite em memória** para validar agrupamentos SQL, filtros e o cálculo ponderado, sem necessidade de senha nem rede. Os testes originais com CSV de exercício não versionado são ignorados quando esses arquivos faltam. Testes de integração na Aiven permanecem condicionados a credenciais autorizadas.

## 9. Evidências necessárias para concluir a entrega

- [ ] Configurar secrets com usuário somente leitura e confirmar conexão TLS.
- [ ] Conferir resultados SQL reais dos quatro indicadores e filtros.
- [ ] Avaliar segurança de hospedagem / exposição do Aiven e privacidade por diferença.
- [ ] Publicar o dashboard em ambiente autorizado (ou demonstrar execução local reproduzível).
- [ ] Inserir URL pública (se houver) no README.
- [ ] Capturar **print real** do dashboard funcionando e incluir na pasta `docs/evidencias` (não substituir por mockup).
- [ ] Escrever análise crítica com resultados numéricos **conferidos** no banco.
- [ ] Ensaio de apresentação de 10 minutos.
