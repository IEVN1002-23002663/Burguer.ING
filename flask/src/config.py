class DevelopmentConfig():
     DEBUG=True
     MYSQL_HOST='localhost'
     MYSQL_USER='Carlos'
     MYSQL_PASSWORD='root'
     MYSQL_DB='burguer_ing'
     MYSQL_CURSORCLASS = 'Cursor'
     JWT_SECRET_KEY = 'BurguerING_Clave_Secreta_Desarrollo_2026'

    # Duración del token: 2 horas
     JWT_EXPIRATION_HOURS = 2

     # Clave para firmar los tokens JWT
    
 
config={
     'development':DevelopmentConfig
}