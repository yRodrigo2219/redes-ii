from socket import AF_INET, SOCK_STREAM, socket
import cfg
import json

# Organiza as informações recebidas para analize do professor
def make_statistics(statsInfo):
    statistics = ''
    for question in statsInfo:
        statistics += f"{question['q']}\n"
        for c in range(len(question['c'])):
            choice = question['c'][c]
            answers = question['a'][c]
            statistics += f"  {choice} -> Foi votada por {answers} estudantes\n"
        statistics += '\n'
    
    return statistics

# Permite que o professor digite as questões da competição
def make_contest():
    contest = []
    while(True):
        userQuestion = input(f'Digite a questão {len(contest) + 1}: ')
        if userQuestion == cfg.cli["exit"]:
            break

        alternatives = []
        answers = []
        print(f'\nAgora será necessário digitar as alternativas, digite \'{cfg.cli["done"]}\' para finalziar a questão!')
        while(True):
            userChoices = input(f'Digite a alternativa {len(alternatives) + 1} para a questão {len(contest) + 1}: ')
            if userChoices == cfg.cli["done"]:
                break

            if userChoices == cfg.cli["exit"]:
                continue

            alternatives.append(f'{len(alternatives) + 1}) {userChoices}')
            answers.append(0)

        contest.append({
            'q': f'{len(contest) + 1}- {userQuestion}',
            'c': alternatives,
            'a': answers,
        })
    
    return contest

def main():
    # Inicia a conexão
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((cfg.server['name'], cfg.server['port']))
    
    # Define tipo de usuario
    request = {}
    userType = input('Deseja se conectar como professor ou aluno? (p/a)\n')[0]
    if userType == 'p': # Caso seja professor
        request['user'] = cfg.UserType.PROFESSOR
        print(f'Agora será necessário digitar as questões, digite \'{cfg.cli["exit"]}\' para encerrar!\n')

        # Faz as questões da competição     
        request['contest'] = make_contest()

        # Envia as questões
        clientSocket.send(json.dumps(request).encode())

        # Recebe o código que deve ser compartilhado
        code = clientSocket.recv(8).decode()
        print(f'\nCódigo: {code}')

        # Decide quando soltar as questões
        input('Pressione Enter para disponibilizar as questões.\n')
        clientSocket.send('1'.encode())

        # Espera os estudantes terminarem de responder
        print('Esperando todos os estudantes terminarem...\n')
        statsInfo = json.loads(clientSocket.recv(4096).decode())

        print(make_statistics(statsInfo)) # Exibe as estatisticas
        
    else: # Caso seja aluno
        request['user'] = cfg.UserType.STUDENT

        # Passa o código necessário
        code = input('Digite o código: ')
        request['contest'] = code
        clientSocket.send(json.dumps(request).encode())

        # Espera o professor liberar as questões
        print('Esperando o inicio da competição...')
        howManyQuestions = int(clientSocket.recv(8).decode())

        # Recebe as questões (uma de cada vez)
        print('Competição iniciada!\n')
        for q in range(howManyQuestions):
            print(clientSocket.recv(4096).decode()) # Imprime a questão
            answer = input('Selecione a alternativa correta: ')
            clientSocket.send(answer.encode()) # Envia respota da questão
        
        print('\nQuestões finalizadas!')

    # Finaliza o cliente
    clientSocket.close()

if __name__ == '__main__':
    main()
