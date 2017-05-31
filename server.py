from flask import Flask
from flask import current_app
import collections

# import Ranking
import rethinkdb as r
import json
from ranking import Ranking
import pandas as pd
app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world'

@app.route('/get_user/<user_id>')
def get_user(user_id):
    r.connect('localhost',28015).repl()
    user = list(r.db('usuarios').table('raw_data').filter({"user_id":int(user_id)}).run())

    return json.dumps(user)
@app.route ('/get_rankings/<user_id>')
def get_rankings(user_id): #ta tendo alguma confusao de dados, usarios nao estao com os dados corretos
    r.connect('localhost',28015).repl()
    #pegando user
    user = list(r.db('usuarios').table('raw_data').filter({"user_id":int(user_id)}).run())
    #pegando registros sem ser o user
    df = list(r.db('usuarios').table('raw_data').filter(lambda user:user["user_id"] != int(user_id)).run())

    df_raw = pd.read_json(json.dumps(df))
    user   = pd.read_json(json.dumps(user))

    del user['id']
    df_json = df_raw
    del df_json['id']
    # del df_raw['id']
    # print(df_json.head())

    user    = preprocessThidDf(user, df_raw)

    df_json = preprocessThidDf(df_json, df_json)
    # raise Exception('xyz')
    tmp_rank = Ranking(user)
    user = tmp_rank.preprocessDataFrame()

    rank = Ranking(df_json)
    df_json = rank.preprocessDataFrame()
    X_treino  = pd.DataFrame(df_json)
    X_teste   = pd.DataFrame(user)

    ranked_data = rank.rank_the_data(X_treino, X_teste)
    filtered_data = rank.filter_ranked_data(ranked_data,min_val=0.80)
    return generateFullJSON(pd.read_json(json.dumps(df)), filtered_data)

def preprocessThidDf(df, complete_df):
    temp_df= pd.DataFrame.copy(complete_df)
    classes = set([x.strip() for y in temp_df['habilidades'] for x in y])
    #aqui ainda nao existe uma coluna pra cada classe
    #criando as colunas com o nome das classes
    for classe in classes: df[classe] = 0

    # # Modifying columns to '1' when habilidade is found

    for i in range(len(df['habilidades'])): # para cada linha, ou seja, cada usuario
        classes_line = df.loc[i,'habilidades'] #pegamos suas habilidades
    #     print(classes_line);
    #     print("-------------")
        for j in range(len(classes_line)): #para cada habilidade daquele usuario
            classe = classes_line[j] #pegamos a atual habilidade do usuario
            if classe in classes: #verificamos se a habilidade atual existe no nosso vetor de classes global
                df.loc[:, (classe)][i] = 1

    del df['habilidades']

    return df
def generateFullJSON(raw_df,filtered_dict):
    #the JSON should return the following structure:
    jsons      = []
    for key,item in filtered_dict.items():
        user_type = raw_df.loc[:,'tipo_user'][key]
        user_id = key
        skills = raw_df.loc[:,'habilidades'][key]
        market = raw_df.loc[:, 'segmento'][key]
        hours = raw_df.loc[:, 'horas_disponiveis'][key]
        codigo = collections.OrderedDict({"user_id": int(user_id), "user_type": user_type,
                  "skills":skills,"market":market,"hours":float(hours),"ratings": []})

        #ordenando pela rating
        ordered_dict = collections.OrderedDict(sorted(item.items(), key= lambda x:x[1],reverse=True))
        #print("Ordered dict", ordered_dict)
        for k,v in ordered_dict.items():

            guess_user_type = raw_df.loc[:, 'tipo_user'][k]
            guess_user_id = k
            guess_skills = raw_df.loc[:,'habilidades'][k]
            guess_market = raw_df.loc[:, 'segmento'][k]
            guess_hours = raw_df.loc[:, 'horas_disponiveis'][k]

            codigo["ratings"].append(collections.OrderedDict({"user_id": int(guess_user_id), "user_type": guess_user_type,
                  "skills":guess_skills,"market":guess_market,"hours":float(guess_hours),"rating":float(v)}))

        jsons.append(codigo)
    return json.dumps(jsons)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
