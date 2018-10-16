import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import logging
import time



LOG_FILENAME = 'logging_HEB.out'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )
logging.debug('HEB ')
logging.debug('*************************************')
logging.debug('Inicio : ' + time.strftime("%d/%m/%Y") + '   ' + (time.strftime("%H:%M:%S")))

f = open(LOG_FILENAME, 'rt')
try:
    body = f.read()
finally:
   f.close()


#**************
# cadena conexion sql server
import pyodbc 
server='tcp:orbisprices.database.windows.net'
database='OrbisPrice';
username='PriceExternalLogin@orbisprices'
password='Pr!c3Ext3rn4l082018'

cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)


cursor = cnxn.cursor()
id_item=0


sql_ligas = 'select * from farmacia_ligas where id_farmacia = 7'
tokens = 'select * from tokens '
cursor.execute(sql_ligas)
result = cursor.fetchall()
tokens = 'select rtrim(ltrim(token)) token,rtrim(ltrim(token_asignado)) token_asignado, tipo from tokens'
cursor.execute(tokens)
tokens = cursor.fetchall()

d=[]
for row in tokens:
    d.append({'token':row[0],'asignado':row[1],'tipo':row[2]})          

df = pd.DataFrame(d)

lab='NA'
sustancia='NA'
presentacion_aux2="NA"
lng=0

for row in result:
        print('row = %r' % (row[2],))
        url=row[2]
        urlx = url[:-1]
        categoria=row[1]
        
        for numero_pagina in range(row[3]):
            
            url_categoria = urlx +  format(numero_pagina+1) 
            
            print(url_categoria)
           
            try:
              page = requests.get(url_categoria)
              soup = BeautifulSoup(page.text, 'html.parser')
            except:
               logging.debug('problema conexion' + url_categoria)
               pass 
            #print (soup)


            
            lista_sku_productos =soup.find_all(class_='price-box')
            lista_nombre_productos = soup.find_all(class_='product-name')
            lista_nombre_lab = soup.find_all(class_= 'shortDescrption_1')
            lista_precio_productos= soup.find_all(class_='price-box')




            lin=0
            producto_nombre_aux = ""
            lab=""
            presentacion=""
            sustancia="NA"
            precio=0
            precio2=0
            item=0
            promocion=""
            sku=""
            plin= 0
            url_imagen=""
            for producto_name in lista_nombre_productos:
                            try:

                                    sku1 = lista_sku_productos[item]

        
                                    for b in sku1.findAll('span',id=True):
                                      sku = b.get('id')
                                    sku = sku.split('-')
                                    sku=sku[-1]
                                    #print(sku)


                                    for a in producto_name.findAll('a',href=True):
                                      url_imagen = a.get('href')
                                    #print(url_imagen)
                                    
                                    
                                    #print(producto_name.text.strip())
                                   
                                    producto_nombre_aux = producto_name.text
                                    lab = lista_nombre_lab[item].text
                                    lab=lab.strip()
                                    producto_nombre_nuevo = producto_nombre_aux.replace("'"," ")

                                    presentacion_aux2=""

                                    lista_precios=lista_precio_productos[item].text

                                    lines = (line.strip() for line in lista_precios.splitlines())
                                        # break multi-headlines into a line each
                                    chunks = lines #(phrase.strip() for line in lines for phrase in line.split("  "))
                                        # drop blank lines
                                    text = '\n'.join(chunk for chunk in chunks if chunk)
                                    
                                   
                                    if len(text.splitlines())> 1 :
                                                  precio = text.splitlines()[2] 
                                    else:
                                                  precio = text.splitlines()[0]

                                   
                                    precio = precio.replace(",","")
                                    precio = precio.replace(" ","") 
                                    precio = precio.replace("MXN","")
                                    precio = precio.replace("$","")
                                    precio=precio.strip()
                                    
                                    producto_nombre_nuevo = producto_nombre_aux.replace("'"," ")
                                    producto_nombre_nuevo= producto_nombre_nuevo.replace("."," ")
                                    producto_nombre_nuevo= producto_nombre_nuevo.replace("(","")                             
                                   
                                   
                                    item = item +1
                                    id_item = id_item +1

                                    #text mining bag of words
                                    words = producto_nombre_nuevo.split()
                                    nombre=producto_nombre_nuevo
                                    contenido=" "
                                    unidades=""
                                    unidades2=""
                                    tipo=""
                                    num_unidades=0
                                

                                    num_word=0
                                

                                    for word in words:
                             
                                       a=word.upper()
                                       try:
                                          b=(df.loc[df['token']==a])
                                          if ( b.iloc[0]['tipo']) == 1:
                                             ban=1
                                             contenido = b.iloc[0]['asignado']
                                             nombre = nombre.replace(word,"")
                                             sustancia=sustancia.replace(word,"")
                                             if  (words[num_word -1].isdigit()):
                                                  unidades = words[num_word -1]
                                                  nombre = nombre.replace(words[num_word -1],"")
                                                  sustancia=sustancia.replace(words[num_word -1],"")
                                             if  (words[num_word + 1].isdigit()):
                                                  unidades = words[num_word +1]
                                                  nombre = nombre.replace(words[num_word +1],"")
                                                  sustancia=sustancia.replace(words[num_word +1],"")

                                                 
                                          else:
                                            if tipo=="":
                                              ban=2
                                              tipo=  b.iloc[0]['asignado']
                                              nombre = nombre.replace(word,"")
                                              sustancia=sustancia.replace(word,"")
                                              if  (words[num_word -1].isdigit()):
                                                  unidades2 = words[num_word -1]
                                                  nombre = nombre.replace(words[num_word -1],"")
                                                  sustancia=sustancia.replace(words[num_word -1],"")
                                                
                                              
                                       except:
                                         pass
         
                                   
                                       if  re.search(r"[0-9]/[0-9]",a) :
                                       
                                            if num_unidades == 0 and ban==2: 
                                                    unidades2=word
                                                    num_unidades=1
                                            else:
                                                    unidades=word
                                            nombre = nombre.replace(word,"")
                                            sustancia=sustancia.replace(word,"")
                                            unidades2 = word[-1]
                                       else:
                                            
                                            if re.search(r"[0-9][0-9]M*",a) or re.search(r"[0-9][0-9]G*",a) :
                                                a = word[-2:]
                                                a = a.upper()
                                                #print(a)
                                                try:
                                                    b=(df.loc[df['token']==a])
                                                    if ( b.iloc[0]['tipo']) == 1:
                                                         contenido = b.iloc[0]['asignado']
                                                         nombre = nombre.replace(word,"")
                                                         sustancia=sustancia.replace(word,"")
                                                    else: 
                                                          tipo=  b.iloc[0]['asignado']
                                                          unidades2 = word[:-2]
                                                          num_unidades=1
                                                          nombre = nombre.replace(word,"")
                                                          sustancia=sustancia.replace(word,"")
                                                except:
                                                    pass
                                                
                                                nombre = nombre.replace(word,"")
                                       num_word = num_word +1 


                      
                                    text = ""
                                    try:
                                      sql = ("insert into Productos values (7," + format(id_item) + ",'" + sku 
                                         + "','" + nombre.strip()
                                         + "','" + producto_nombre_nuevo.strip()
                                         + "','" + lab + "','"
                                         +  sustancia + "','" + presentacion_aux2.strip()
                                         + "','" + contenido.strip()
                                         + "','" + unidades
                                         + "','" + tipo.strip()
                                         + "','" + unidades2 
                                         + "'," + format(precio) + "," + format(categoria)
                                         + ", GETDATE(),'" + url_imagen + "' )" )
                                      #print(sql)
                                      cursor.execute(sql)
                                      cursor.commit()
                                    except:
                                        logging.debug('error al grabar el registro datos:',sql)
                                        pass

                                    lin=0
                                    producto = ""
                                    lab=""
                                    presentacion=""
                                    sustancia=""
                                    precio = 0
                                    plin=0

                            except:
                              logging.debug('error al leer página')
                              pass

try:
    sql = ("exec SP_Actualiza_catalogo 7")
    cursor.execute(sql)
    cursor.commit()
except:
  logging.debug('error al actualizar el catalogo datos:',)
pass



     
logging.debug('fin Farmacia del ahorro : ' + (time.strftime("%H:%M:%S")))
           

                
