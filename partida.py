import streamlit as st  
import pandas as pd
import numpy as np
import random
import time
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import poisson 

st.set_page_config(
    page_title = 'Previsão Esportiva - Copa do Mundo Qatar 2022',
    page_icon = '⚽',
    initial_sidebar_state = "expanded",
    menu_items = {
        'About': 'https://www.previsaoesportiva.com.br', 
    }
)

dados_variaveis = pd.read_excel('dados_previsao_esportiva.xlsx', sheet_name ='grupos')
fifa = dados_variaveis['Ranking Point']
fifa.index = dados_variaveis['Seleção']

a, b = min(fifa), max(fifa) 
fa, fb = 0.05, 1 
b1 = (fb - fa)/(b-a) 
b0 = fb - b*b1
fatorFifa = b0 + b1*fifa 

fatorFifa.sort_values(ascending = False)

fifa = dados_variaveis['RankingELO']
fifa.index = dados_variaveis['Seleção']

a, b = min(fifa), max(fifa) 
fa, fb = 0.05, 1 
b1 = (fb - fa)/(b-a) 
b0 = fb - b*b1
fatorELO = b0 + b1*fifa 

fatorELO.sort_values(ascending = False)

def Fator(dados, var, K):
    res = K * (dados[var] - min(dados[var]))/(max(dados[var]) - min(dados[var])) + (1 - K)
    res.index = dados_variaveis['Seleção']
    return res

fatorMercado = Fator(dados_variaveis, 'Market Value', K = 0.1) 
fatorATQ = Fator(dados_variaveis, 'ATAQUE', K = 0.05) 
fatorDEF = 1 - Fator(dados_variaveis, 'DEFESA', K = 0.05) + 0.95
fatorCopa = Fator(dados_variaveis, 'Copas2', K = 0.1)
fatorTendencia = Fator(dados_variaveis, 'Saldo', K = 0.1)

fatores =  (fatorMercado * fatorDEF * fatorATQ * fatorCopa * fatorTendencia)

forca = (0.5*fatorFifa + 0.5*fatorELO) * fatores
forca = forca/max(forca)
forca = 0.7*(forca - min(forca))/(max(forca) - min(forca)) + 0.30
forca = forca.sort_values(ascending = False)
forca 

lista07 = ['0', '1', '2', '3', '4', '5', '6', '7+']

def Resultado(gols1, gols2):
	if gols1 > gols2:
		res = 'V'
	if gols1 < gols2:
		res = 'D' 
	if gols1 == gols2:
		res = 'E'       
	return res

def MediasPoisson(sele1, sele2):
	forca1 = forca[sele1]
	forca2 = forca[sele2]
	fator = forca1/(forca1 + forca2)
	mgols = 2.75
	l1 = mgols*fator
	l2 = mgols - l1
	return [fator, l1, l2]
	
def Distribuicao(media, tamanho = 7):
	probs = []
	for i in range(tamanho):
		probs.append(poisson.pmf(i,media))
	probs.append(1-sum(probs))
	return pd.Series(probs, index = lista07)

def ProbabilidadesPartida(sele1, sele2):
	fator, l1, l2 = MediasPoisson(sele1, sele2)
	d1, d2 = Distribuicao(l1), Distribuicao(l2)  
	matriz = np.outer(d1, d2)    #   Monta a matriz de probabilidades

	vitoria = np.tril(matriz).sum()-np.trace(matriz)    #Soma a triangulo inferior
	derrota = np.triu(matriz).sum()-np.trace(matriz)    #Soma a triangulo superior
	probs = np.around([vitoria, 1-(vitoria+derrota), derrota], 3)
	probsp = [f'{100*i:.1f}%' for i in probs]

	nomes = ['0', '1', '2', '3', '4', '5', '6', '7+']
	matriz = pd.DataFrame(matriz, columns = nomes, index = nomes)
	matriz.index = pd.MultiIndex.from_product([[sele1], matriz.index])
	matriz.columns = pd.MultiIndex.from_product([[sele2], matriz.columns]) 
	output = {'seleção1': sele1, 'seleção2': sele2, 
			 'f1': forca[sele1], 'f2': forca[sele2], 'fator': fator, 
			 'media1': l1, 'media2': l2, 
			 'probabilidades': probsp, 'matriz': matriz}
	return output

def Pontos(gols1, gols2):
	rst = Resultado(gols1, gols2)
	if rst == 'V':
		pontos1, pontos2 = 3, 0
	if rst == 'E':
		pontos1, pontos2 = 1, 1
	if rst == 'D':
		pontos1, pontos2 = 0, 3
	return pontos1, pontos2, rst


def Jogo(sele1, sele2):
	fator, l1, l2 = MediasPoisson(sele1, sele2)
	gols1 = int(np.random.poisson(lam = l1, size = 1))
	gols2 = int(np.random.poisson(lam = l2, size = 1))
	saldo1 = gols1 - gols2
	saldo2 = -saldo1
	pontos1, pontos2, result = Pontos(gols1, gols2)
	placar = '{}x{}'.format(gols1, gols2)
	return [gols1, gols2, saldo1, saldo2, pontos1, pontos2, result, placar]


listaselecoes = dados_variaveis['Seleção'].tolist()  
listaselecoes.sort()
listaselecoes2 = listaselecoes.copy()

######## COMEÇO DO APP

paginas = ['Principal', 'Tabelas']
pagina = st.sidebar.radio('Selecione a página', paginas)



if pagina == 'Principal':

	a1, a2 = st.columns([1,4])
	a1.image('previsaoesportivalogo.png', width = 200)
	a2.markdown("<h2 style='text-align: right; color: #5C061E; font-size: 32px;'>Copa do Mundo Qatar 2022 🏆  </h1>", unsafe_allow_html=True)
	st.markdown('---')
	st.markdown("<h2 style='text-align: center; color: #0f54c9; font-size: 40px;'>Probabilidades dos Jogos ⚽<br>  </h1>", unsafe_allow_html=True)

	st.markdown('---')
	tipojogo = st.radio('Escolha o tipo de jogo', ['Jogo da Fase de Grupos', 'Jogo do Mata-Mata'])
	st.markdown('---')

	j1, j2 = st.columns (2)
	selecao1 = j1.selectbox('--- Escolha a primeira Seleção ---', listaselecoes) 
	listaselecoes2.remove(selecao1)
	selecao2 = j2.selectbox('--- Escolha a segunda Seleção ---', listaselecoes2, index = 1)
	 
	st.markdown('---')
 


	jogo = ProbabilidadesPartida(selecao1, selecao2)
	prob = jogo['probabilidades']
	matriz = jogo['matriz']

 
	if tipojogo == 'Jogo da Fase de Grupos':
		col1, col2, col3, col4, col5 = st.columns(5)
		col1.image(dados_variaveis[dados_variaveis['Seleção'] == selecao1]['LinkBandeira2'].iloc[0]) 
		col2.markdown(f"<h5 style='text-align: center; color: #1a1a1a; font-weight: bold; font-size: 25px;'>{selecao1}<br>  </h1>", unsafe_allow_html=True)
		col2.markdown(f"<h2 style='text-align: center; color: #0f54c9; font-weight: bold; font-size: 50px;'>{prob[0]}<br>  </h1>", unsafe_allow_html=True)
		col3.markdown(f"<h2 style='text-align: center; color: #6a6a6b; font-weight: 100; font-size: 15px;'>Empate<br>  </h1>", unsafe_allow_html=True)
		col3.markdown(f"<h2 style='text-align: center; color: #6a6a6b;                    font-size: 30px;'>{prob[1]}<br>  </h1>", unsafe_allow_html=True)
		col4.markdown(f"<h5 style='text-align: center; color: #1a1a1a; font-weight: bold; font-size: 25px;'>{selecao2}<br>  </h1>", unsafe_allow_html=True) 
		col4.markdown(f"<h2 style='text-align: center; color: #0f54c9; font-weight: bold; font-size: 50px;'>{prob[2]}<br>  </h1>", unsafe_allow_html=True) 
		col5.image(dados_variaveis[dados_variaveis['Seleção'] == selecao2]['LinkBandeira2'].iloc[0])
 
	if tipojogo == 'Jogo do Mata-Mata':
		col1, col2, col3, col4, col5 = st.columns(5)
		col1.image(dados_variaveis[dados_variaveis['Seleção'] == selecao1]['LinkBandeira2'].iloc[0]) 
		col2.markdown(f"<h5 style='text-align: center; color: #1a1a1a; font-weight: bold; font-size: 25px;'>{selecao1}<br>  </h1>", unsafe_allow_html=True)
		aux1 = round(float(prob[0][:-1])+float(prob[1][:-1])/2, 1)
		aux2 = str(aux1) + '%' 
		col2.markdown(f"<h2 style='text-align: center; color: #0f54c9; font-weight: bold; font-size: 50px;'>{aux2}<br>  </h1>", unsafe_allow_html=True)
		col3.markdown(f"<h2 style='text-align: center; color: #6a6a6b; font-weight: 100; font-size: 15px;'> <br>  </h1>", unsafe_allow_html=True)
		col3.markdown(f"<h2 style='text-align: center; color: #6a6a6b;                    font-size: 30px;'>vs<br>  </h1>", unsafe_allow_html=True)
		col4.markdown(f"<h5 style='text-align: center; color: #1a1a1a; font-weight: bold; font-size: 25px;'>{selecao2}<br>  </h1>", unsafe_allow_html=True) 
		aux3 = round(100 - aux1, 1)
		aux4 = str(aux3) + '%' 
		col4.markdown(f"<h2 style='text-align: center; color: #0f54c9; font-weight: bold; font-size: 50px;'>{aux4}<br>  </h1>", unsafe_allow_html=True) 
		col5.image(dados_variaveis[dados_variaveis['Seleção'] == selecao2]['LinkBandeira2'].iloc[0])

	st.markdown('---')
 


	def aux(x):
		return f'{str(round(100*x,2))}%'

	#st.table(matriz.applymap(aux))
 


	
	fig, ax = plt.subplots()
	sns.heatmap(matriz.reset_index(drop=True), ax=ax, cmap = 'Blues', annot = 100*matriz , fmt=".2f", xticklabels = lista07, yticklabels = lista07) 
	ax.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = True, labeltop=True )
	ax.xaxis.set_label_position('top')
	ax.set_xlabel('Gols ' + selecao2, fontsize=15, color = 'gray')	
	ax.set_ylabel('Gols ' + selecao1, fontsize=15, color = 'gray')	
	ax.set_xticklabels(ax.get_xticklabels(), rotation = 0, fontsize = 8, color = 'gray')
	ax.set_yticklabels(ax.get_yticklabels(), rotation = 0, fontsize = 8, color = 'gray' )


	st.markdown("<h2 style='text-align: center; color: #0f54c9; font-size: 40px;'> Probabilidades dos Placares ⚽<br>  </h1>", unsafe_allow_html=True) 
	st.write(fig)

	st.markdown('---')

	placar = np.unravel_index(np.argmax(matriz, axis=None), matriz.shape) 

	st.markdown("<h2 style='text-align: center; color: #0f54c9; font-size: 40px;'> Placar Mais Provável ⚽<br>  </h1>", unsafe_allow_html=True)
	
	st.markdown(' ')

	col1, col2, col3 = st.columns([1,5,1])
	col1.image(dados_variaveis[dados_variaveis['Seleção'] == selecao1]['LinkBandeira2'].iloc[0]) 
	#col2.header(selecao1) 
	col2.markdown(f"<h2 style='text-align: center; color: #1a1a1a; font-size: 40px;'>{selecao1} {placar[0]}x{placar[1]} {selecao2}<br>  </h1>", unsafe_allow_html=True)
	#col4.header(selecao2)
	col3.image(dados_variaveis[dados_variaveis['Seleção'] == selecao2]['LinkBandeira2'].iloc[0]) 



	st.markdown('---')

	st.markdown('Trabalho desenvolvido pela Equipe Previsão Esportiva - acesse www.previsaoesportiva.com.br 🔗')

	#bandeira1, nome1, prob, empate, prob, nome2, bandeira2
	#matriz de probabilidades do jogo
	#placar mais provável

if pagina == 'Tabelas': 

	atualizacoes = ['Início da Copa', 'Pós Primeira Rodada']
	a = st.radio('Selecione a Atualização', atualizacoes, index = 2)

	if a == 'Início da Copa':
		dados0 = pd.read_excel('dados_previsao_esportiva.xlsx', sheet_name ='grupos', index_col=0) 
		dados1 = pd.read_excel('dados/outputSimulaçõesCopa(n=1000000).xlsx', index_col=0) 
		dados2 = pd.read_excel('dados/outputJogadoresArtilharia(n=1000000).xlsx', index_col=0) 
		dados3 = pd.read_excel('dados/outputFinaisMaisProvaveis(n=1000000).xlsx', index_col=0) 
		dados4 = pd.read_excel('dados/outputProbPorEtapa(n=1000000).xlsx', index_col=0) 
		dados5 = pd.read_excel('dados/outputTabelaJogosPROBS.xlsx', index_col=0) 

		tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(['Dados das Seleções', "Simulações da Copa", "Artilheiro", "Finais Mais Prováveis",  'Probabilidades por Etapa', 'Tabela de Jogos'])

		with tab0:
			st.header("Dados das Seleções") 
			st.write(dados0, height = 900)

		with tab1:
			st.header("Simulações da Copa") 
			st.write(dados1, height = 900)

		with tab2:  
			st.header("Previsões do Artilheiro")  
			st.write(dados2)

		with tab3:  
			st.header("Finais Mais Prováveis")  
			st.write(dados3) 

		with tab4:  
			st.header("Probabilidades por Etapa")  
			st.write(dados4) 

		with tab5:  
			st.header("Tabela de Jogos")  
			st.write(dados5[['grupo', 'seleção1', 'probV', 'probE', 'probD','seleção2']])  

	if a == 'Pós Primeira Rodada':
		dados1 = pd.read_excel('dados/R1outputSimulaçõesCopa(n=1000000).xlsx', index_col=0) 
		dados2 = pd.read_excel('dados/R1outputJogadoresArtilharia(n=1000000).xlsx', index_col=0) 
		dados3 = pd.read_excel('dados/R1outputFinaisMaisProvaveis(n=1000000).xlsx', index_col=0) 
		dados4 = pd.read_excel('dados/R1outputProbPorEtapa(n=1000000).xlsx', index_col=0) 
		dados5 = pd.read_excel('dados/R1outputTabelaJogosPROBS.xlsx', index_col=0) 
		dados6 = pd.read_excel('dados/R1outputAvançoPorEtapa.xlsx', index_col=0) 

		tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Simulações da Copa", 'Artilharia', "Finais Mais Prováveis",  'Probabilidades por Etapa', 'Tabela de Jogos','Probabilidades de Avanço'])
 
		with tab1:
			st.header("Simulações da Copa") 
			st.write(dados1, height = 900)

		with tab2:  
			st.header("Previsões do Artilheiro")  
			st.write(dados2)

		with tab3:  
			st.header("Finais Mais Prováveis")  
			st.write(dados3) 

		with tab4:  
			st.header("Probabilidades por Etapa")  
			st.write(dados4) 

		with tab5:  
			st.header("Tabela de Jogos")  
			st.write(dados5[['grupo', 'seleção1', 'probV', 'probE', 'probD','seleção2']])  

		with tab6:  
			st.header("Probabilidades de Avanço")  
			st.write(dados6) 



	if a == 'Pós Segunda Rodada':
		dados1 = pd.read_excel('dados/R2outputSimulaçõesCopa(n=1000000).xlsx', index_col=0) 
		dados2 = pd.read_excel('dados/R1outputJogadoresArtilharia(n=1000000).xlsx', index_col=0) 
		dados3 = pd.read_excel('dados/R2outputFinaisMaisProvaveis(n=1000000).xlsx', index_col=0) 
		dados4 = pd.read_excel('dados/R2outputProbPorEtapa(n=1000000).xlsx', index_col=0) 
		dados5 = pd.read_excel('dados/R2outputTabelaJogosPROBS.xlsx', index_col=0) 
		dados6 = pd.read_excel('dados/R2outputAvançoPorEtapa.xlsx', index_col=0) 

		tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Simulações da Copa", 'Artilharia', "Finais Mais Prováveis",  'Probabilidades por Etapa', 'Tabela de Jogos','Probabilidades de Avanço'])
 
		with tab1:
			st.header("Simulações da Copa") 
			st.write(dados1, height = 900)

		with tab2:  
			st.header("Previsões do Artilheiro")  
			st.write(dados2)

		with tab3:  
			st.header("Finais Mais Prováveis")  
			st.write(dados3) 

		with tab4:  
			st.header("Probabilidades por Etapa")  
			st.write(dados4) 

		with tab5:  
			st.header("Tabela de Jogos")  
			st.write(dados5[['grupo', 'seleção1', 'probV', 'probE', 'probD','seleção2']])  

		with tab6:  
			st.header("Probabilidades de Avanço")  
			st.write(dados6) 

