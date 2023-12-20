import requests
import psycopg2
import os
from dotenv import load_dotenv
import json

load_dotenv()  
conn = psycopg2.connect(
host=os.getenv('DB_HOST'),
user=os.getenv('DB_USER'),
password=os.getenv('DB_PASS'),
dbname=os.getenv('DB_NAME'),
port=os.getenv('DB_PORT'))

cur = conn.cursor()

class api_to_db:
    def __init__(self):
        self.mediabiasfactcheck_url = "https://political-bias-database.p.rapidapi.com/MBFCdata"
        self.allsides_url = "https://political-bias-database.p.rapidapi.com/ASdata"

        self.mediabiasfactcheck_headers = {
	    "X-RapidAPI-Key": "204f3bb9b4mshb9db242fa2fb406p1c0fcajsn11cff7885fec",
	    "X-RapidAPI-Host": "political-bias-database.p.rapidapi.com"}
        self.allsides_headers = {
	    "X-RapidAPI-Key": "204f3bb9b4mshb9db242fa2fb406p1c0fcajsn11cff7885fec",
	    "X-RapidAPI-Host": "political-bias-database.p.rapidapi.com"}

        # self.allsides_response = requests.get(self.allsides_url, headers=self.allsides_headers)
        # self.mediabiasfactcheck_response = requests.get(self.mediabiasfactcheck_url, headers=self.mediabiasfactcheck_headers)
        
        # self.allsides_data = self.allsides_response.json()
        # self.mediabiasfactcheck_data = self.mediabiasfactcheck_response.json() 
      

    def create_table(self, cur, conn, table_name): #depending on table_name passed, this script pulls the API response
        table_name = table_name
        if table_name == 'mediabiasfactcheck':
            mediabiasfactcheck_response = requests.get(self.mediabiasfactcheck_url, headers=self.mediabiasfactcheck_headers)
            data = mediabiasfactcheck_response.json()
        elif table_name == 'allsides':
            allsides_response = requests.get(self.allsides_url, headers=self.allsides_headers)
            data = allsides_response.json()
        else:
            raise ValueError(f"Table '{table_name}' doesn't exist.")
        
        try:
            columns = data[0] #this accesses the first column of the table passed through
        except (KeyError, IndexError) as e:
            print(f"Error accessing data: {e}")
        

        create_query = f'CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, user_comments VARCHAR, ' #this is the initial 'create table' syntax that will be modified further with the for loop
        create_data = []

        if table_name == 'allsides': #this adds to the create_query initial text to complete it depending on which table is being passed
            for column_name in columns.keys():
                if column_name == 'agreement' or column_name == 'disagreement':
                    create_query += f'{column_name} INTEGER, '
                    create_data.append(column_name)
                else:
                    create_query += f'{column_name} VARCHAR, '
                    create_data.append(column_name)
        else:
            for column_name in columns:
                create_query += f'{column_name} VARCHAR, '
                create_data.append(column_name)
             
        create_query = create_query.rstrip(', ') + ')'

        cur.execute(create_query)
        conn.commit()


    def populate_table(self, cur, conn, table_name):
        table_name = table_name
        if table_name == 'mediabiasfactcheck':
            self.mediabiasfactcheck_response = requests.get(self.mediabiasfactcheck_url, headers=self.mediabiasfactcheck_headers)
            self.mediabiasfactcheck_data = self.mediabiasfactcheck_response.json() 

            columns = ', '.join(self.mediabiasfactcheck_data[0].keys())
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({', '.join(['%s']*len(mediabiasfactcheck_data[0]))})"

            for dict_items in mediabiasfactcheck_data:
                # In the DB, all the names of news organizations under the "name" column have a ' - ' and some text afterwards. I want to keep just the text left of the ' - ' divider
                if 'name' in dict_items and ' \u2013' in dict_items['name']:
                    dict_items['name'] = dict_items['name'].split(' \u2013', 1)[0]
                    print(dict_items['name'])
                    insert_values = tuple(dict_items.values())
                    cur.execute(insert_query, insert_values)
                else:
                    dict_items['name'] = dict_items['name']
            conn.commit()
               
        
        elif table_name == 'allsides':
            allsides_response = requests.get(self.allsides_url, headers=self.allsides_headers)
            allsides_data = allsides_response.json()
            columns = ', '.join(allsides_data[0].keys())
            insert_query = f'''INSERT INTO {table_name} ({columns}) 
            VALUES ({', '.join(['%s']*len(allsides_data[0]))})'''

            for dict_items in allsides_data:
                insert_values = tuple(dict_items.values())
                insert_values = tuple(dict_items.values())
                cur.execute(insert_query, insert_values)
                #print(insert_values)
                conn.commit()       
        else:
            raise ValueError(f"Table '{table_name}' doesn't exist.") 
     


source = api_to_db()
#source.create_table(cur, conn, 'allsides')

#source.populate_table(cur, conn, 'allsides')
#source.populate_table(cur, conn, 'mediabiasfactcheck')

cur.close()
conn.close()