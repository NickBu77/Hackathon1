import requests
import psycopg2
import os
from dotenv import load_dotenv
import model
from rich.console import Console
from rich.markup import escape


class UserInterface:
    def show_user_interface(self):
        self.console = Console()

        self.link_1 = "https://mediabiasfactcheck.com/"
        self.link_2 = "https://www.allsides.com/unbiased-balanced-news"
        self.ascontactlink = "https://www.allsides.com/contact"
        self.mbfccontactlink ="https://mediabiasfactcheck.com/contact/"
        print('\n')
        self.console.print(f"In these eventful times, the fast-paced 24/7 news cycle and state-sponsored "
             f"misinformation on social media, it is difficult to know which sources to trust. "
             f"This program partners [link={self.link_1}]Media Bias Fact Check[/link] and "
             f"[link={self.link_2}]All Sides[/link], two websites that track media bias and "
             f"give you an insight into a bias the website may have.")
        print('\n')
        self.link_input = input(f'To continue, provide a link to an article you have and we will analyze it: ').strip()


    def run_program(self):
        self.show_user_interface()
        link_parts = self.link_input.split('.')
        if len(link_parts) >= 2:
            website = link_parts[-2]  # Take the middle part if there are at least two parts
        elif len(link_parts) == 1:
            website = link_parts[0]  # Take the first part after splitting by '.'
        else:
            website = self.link_input  # If just one part, use the entire link

        
        load_dotenv()  
        conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        dbname=os.getenv('DB_NAME'),
        port=os.getenv('DB_PORT'))

        cur = conn.cursor()

        select_query = '''
            SELECT 
                CASE WHEN mbdf.name IS NULL THEN a.name ELSE mbdf.name END AS name, 
                mbdf.url AS url, 
                mbdf.bias AS "mbfc - bias", 
                a.bias AS "all sides - bias", 
                a.agreement AS "all sides - agreement", 
                a.disagreement AS "all sides - disagreement",
                mbdf.factual AS "mbfc - factual", 
                mbdf.credibility AS "mbfc - credibility",
                mbdf.user_comments as "user comments",
                mbdf.profile AS profile_link,
                a.allsidesurl as as_link
            FROM 
                mediabiasfactcheck mbdf 
            FULL JOIN 
                allsides a 
            ON 
                mbdf.name = a.name
            WHERE 
                mbdf.url LIKE %s
                '''
        
        cur.execute(select_query, (f'%{website}%',))
        results = cur.fetchall() 
        news_source = ''
        if len(results) > 1:
            print('We have several potential matches.')
            print('Select the news source you are searching for: ')
            choices_dict = {}
            for i, result in enumerate(results):
                print(f'Type {i} for {result[0]}')
                choices_dict[i] = result[1]
               #print(choices_dict)

            choice = int(input('Your choice here: ').strip())
            news_source = choices_dict[choice]
            cur.execute(select_query, (f'%{news_source}%',))
            results = cur.fetchone()
        else: 
            news_source = website
            cur.execute(select_query, (f'%{news_source}%',))
            results = cur.fetchone()


        r_name = results[0]
        r_url = results[1]
        if not r_url.startswith("http://") and not r_url.startswith("https://"):
            r_url = "https://." + r_url
        r_mbfc_bias = results[2]
        r_allsides_bias = results[3]
        r_allsides_agreement = results[4]
        r_allsides_disagreement = results[5]
        r_mbfc_factuality =  results[6] 
        r_mbfc_credibility = results[7] 
        r_mbfc_user_comments = results[8]
        r_profile_link = results[9]
        r_as_link = results[10]
        if not r_profile_link.startswith("http://") and not r_profile_link.startswith("https://"):
            r_profile_link = "https://." + r_url
        
        r_bias_explanation = ''
        if r_mbfc_bias == "left-center":
            r_bias_explanation = (f'''
            This media source has a slight to moderate liberal bias. It often publishes factual 
            information that utilizes loaded words (wording that attempts to influence an audience 
            by appeals to emotion or stereotypes) to favor liberal causes.''')
            
        elif r_mbfc_bias == "left":
            r_bias_explanation = (f'''
            This media source has a moderately to strongly biased toward liberal causes through story 
            selection and/or political affiliation. It may utilize strong loaded words (wording that 
            attempts to influence an audience by using appeal to emotion or stereotypes), publish 
            misleading reports and omit reporting of information that may damage liberal causes.''')


        elif r_mbfc_bias == "right-center":
            r_bias_explanation = (f'''
            This media source is slightly to moderately conservative in bias. It often publishes 
            factual information that utilizes loaded words (wording that attempts to influence an 
            audience by using appeal to emotion or stereotypes) to favor conservative causes.''')
            
        elif r_mbfc_bias == "right":
            r_bias_explanation = (f'''
            This media source is moderately to strongly biased toward conservative causes through 
            story selection and/or political affiliation. It may utilize strong loaded words (wording 
            that attempts to influence an audience by using appeal to emotion or stereotypes), publish 
            misleading reports and omit reporting of information that may damage conservative causes.''')

        elif r_mbfc_bias in ["conspiracy", "extreme-left", "extreme-right"]:
            r_bias_explanation =  (f'''
            A questionable source exhibits one or more of the following: extreme bias, consistent 
            promotion of propaganda/conspiracies, poor or no sourcing to credible information, a 
            complete lack of transparency, and/or is fake news. Fake News is the deliberate attempt 
            to publish hoaxes and/or disinformation for profit or influence. Sources listed in this 
            category may be untrustworthy and should be fact-checked on a per-article basis.''')

        elif r_mbfc_bias == "pro-science":
            r_bias_explanation = (f'''
            "This source consists of legitimate science that is evidence-based through the use of 
            credible scientific sourcing. It follows the scientific method, is unbiased and does 
            not use emotional words. This source also respects the consensus of experts in the given 
            scientific field and strives to publish peer-reviewed science. This source may have a 
            slight political bias but adheres to scientific principles.''')

        elif r_mbfc_bias == "satire":
            r_bias_explanation = (f'''
            This source exclusively uses humor, irony, exaggeration, or ridicule to expose and 
            criticize people’s stupidity or vices, particularly in the context of contemporary 
            politics and other topical issues. This source is clear that it is satire and does 
            not attempt to deceive.''')

        elif r_mbfc_bias == "center":
            r_bias_explanation = (f'''
            This source has minimal bias and uses very few loaded words (wording that attempts 
            to influence an audience by using appeal to emotion or stereotypes). The reporting 
            is factual and usually sourced. This is among one of the most credible news sources.''')
        
        else:
            r_bias_explanation = ("MBFC does not provide a bias score to this news source.")

        if r_allsides_bias is not None:
            allsides_text = (f'''
            [link={self.link_2}]All Sides[/link] ranks the bias of {r_name} as '{r_allsides_bias}'.

            To visit the All Sides profile page for {r_name}, click [link={r_as_link}]here[/link].
            If you have an issue with this rating, make your voice heard. Please [link={self.ascontactlink}]contact All Sides[/link]. 
            ''')
        else:
            allsides_text = ''

        final_text = (f'''
        The news source is [link={r_url}]{r_name}[/link]

        According to [link={self.link_1}]Media Bias Fact Check[/link], this website is politically on the '{r_mbfc_bias}'.
        It is ranked '{r_mbfc_factuality}' on the factuality scale and is considered a source with '{r_mbfc_credibility}'.

        {r_bias_explanation}

        To visit the Media Bias Fact Check profile page for {r_name}, click [link={r_profile_link}]here[/link].
        If you have an issue with this rating, make your voice heard. Please [link={self.mbfccontactlink}]contact Media Bias Fact Check[/link]. 

        {allsides_text}

        ''')

        return self.console.print(final_text)

        
    def insert_table(self, cur, conn, table_name): #depending on table_name passed, this script pulls the API response
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


        
#dict1 = {304: ('North Korea Times', 'www.northkoreatimes.com', 'center', None, None, 'mostly', 'medium credibility'), 305: ('North Birmingham Times', 'northbirminghamtimes.com/', 'right-center', None, None, 'mixed', 'low credibility'), 306: ('Magic Valley Times', 'magicvalleytimes.com/', 'right-center', None, None, 'mixed', 'low credibility'), 307: ('High River Times', 'www.highrivertimes.com/', 'right-center', None, None, 'high', 'high credibility')}

#print(dict1[305])
UI = UserInterface()
UI.run_program()


#source.create_table(cur, conn, 'allsides')

#source.populate_table(cur, conn, 'allsides')
#source.populate_table(cur, conn, 'mediabiasfactcheck')

