# Разбор сервиса Pass Vault
## Уязвимость 1: IDOR
Рассмотрим ручку для получения пароля
```python
@router.get("/api/passwords/{password_id}", response_model=PasswordRead)
def read_password(password_id: int, current_user: UserBase = Depends(get_current_user), db: Session = Depends(get_db)):
    password = crud.get_password(db, password_id)
    if password is None:
        raise HTTPException(status_code=404, detail="Password not found")
    return password
```
Рассмотрим функцию в **/backend/app/crud.py**
```python
def get_password(db: Session, password_id: int):
    return db.query(models.Password).filter(
        models.Password.id == password_id
    ).first()
```
Эта функция отвечает за получение определенного пароля по **id** записи в таблице **passwords**
Обратим внимания, что в качестве аргумента метода filter() указывается только password_id.  
Проверка принадлежности пароля к пользователю от лица которого пришел запрос не происходит.  

### Эксплуатация:
Можем сделать вывод, что при GET запросе на **/api/passwords/{password_id}** в качестве password_id можно указать любой уже существующий id и получить пароли других пользователей.

### Защита:
Добавить дополнительные проверки на принадлежность пароля к пользователю, который запрашивает его.

## Уязвимость 2: Предсказуемо-рандомное значение SECRET_KEY
Рассмотрим **/backend/app/auth.py**
```python
random.seed(521337)
SECRET_KEY = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=32))
```
В этом отрывке кода описывается рандомная генерация SECRET_KEY, однако, строчкой выше задается SEED для псевдослучайного генератора чисел. При знании сида, мы можем предсказать все сгенерированные значения.  
Таким образом, SECRET_KEY всегда равен ```gAcx_CWu2mDy8s1`G:!0>i"nRv960-]\\```  

### Эксплуатация:
Имея такое знание, мы можем выпускать подписанные JWT с логинами ботов взятых из публичной атак даты (ручка /api/client/attack_data на борде) и читать все их пароли.

### Защита:
Сделать действительно рандомную генерацию SECRET_KEY

## Уязвимость 3: ORM Injection
В данном сервисе взаимодействие с базой данных происходит не прямыми SQL запросами, а с применением ORM.  
Казалось бы, что это идеальное решение для предотвращения SQL инъекций, но в этом сервисе есть одно место уязвимое к подобной атаке.
Рассмотрим **/backend/app/crud.py**
```python
def get_passwords(db: Session, user_id: int, orderByValue: str):
    return db.query(models.Password).filter(models.Password.user_id == user_id).order_by(text(orderByValue)).all()
```
Самым важным здесь является вызов метода **.order_by(text(orderByValue))**
Из документации мы узнаем:  
`text(text) - Construct a new TextClause clause, representing a textual SQL string directly.`  
  
Получается, всё, что обёрнуто в функцию text() будет подставлено в конченый запрос к базе без изменений и экранирования. Таким образом, мы получаем PostgreSQL boolean-based blind SQL инъекцию через аргумент в **ORDER BY**.

### Эксплуатация:
`sqlmap -u http://127.0.0.1/api/passwords?orderByValue=website --cookie='access_token=<your_access_token>' --technique=B --level 3 --dump -T passwords`

### Защита:
Исключиьт использование функции text()
