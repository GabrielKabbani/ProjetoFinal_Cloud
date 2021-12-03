import requests

url = str(input('Cole aqui o DNS do load balancer: '))
choice = input(
    """O que deseja fazer?\n\n
    Ao escrever POST, será solicitado o titulo, descricao, e data para serem enviados, \n
    Ao escrever GET, serão trazidas todas as tasks, \n
    E ao escrever DELETE, todas as tasks serão deletadas.\n\n
    Escreva a sua escolha da mesma forma que está escrito acima em letra maiúscula: """
    )

if(str(choice) == "DELETE"):
    print("Você escolheu DELETE")
    result = requests.delete("http://{0}:80/tasks/request/tasks".format(url))
    print(result.text)
elif(str(choice) == "GET"):
    print("Você escolheu GET")
    result = requests.get("http://{0}:80/tasks/request/tasks".format(url))
    print(result.text)
elif(str(choice) == "POST"):
    print("Você escolheu POST")
    title = str(input("Insira um titulo: \n"))
    pubdate = "{0}/{1}/{2} {3}:{4}".format(input("Qual ano?: "),input("Qual mês?: "),input("Qual dia?: "),input("Qual hora?: "),input("Qual minuto?: "))
    description = str(input("Insira uma descricao: \n"))
    result = requests.post("http://{0}:80/tasks/request/tasks".format(url), json={"title": title, "pub_date": pubdate, "description": description})
    print(result.text)
