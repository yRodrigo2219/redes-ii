from socket import AF_INET, SOCK_STREAM, socket
import cfg
import json
import threading
from random import randint


def random_id():
    r = randint(0, 999999) # Gera um número com 6 ou menos digitos
    r = str(r).zfill(6) # Preenche com 0s a esquerda

    return r

def main():
    runningContests = {}
    db = threading.Semaphore()

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((cfg.server["name"], cfg.server["port"]))
    serverSocket.listen()

    def connection_thread(connectionSocket, addr):
        request = json.loads(connectionSocket.recv(4096).decode())
        if cfg.UserType(request['user']) == cfg.UserType.PROFESSOR: # Caso seja professor
            contest = request['contest']
            contestId = random_id()
            db.acquire()
            c = runningContests[contestId] = {
                'contest': contest,
                'connected-students': 0,
                'hasStarted': threading.Semaphore(0),
                'sendStatistics': threading.Semaphore(0),
            }
            db.release()
            print(f'Nova competição recebida! Código: {contestId}')
            connectionSocket.send(contestId.encode())

            connectionSocket.recv(1).decode() # Espera disponibilizar as questões
            c['hasStarted'].release(c['connected-students']) # Permite que os estudantes respondam
            
            # Espera todos os estudantes terminarem de responder
            c['sendStatistics'].acquire()
            # Envia as estatisticas
            connectionSocket.send(json.dumps(c['contest']).encode())

        else: # Caso seja aluno
            contestId = request['contest']
            print(f'Novo aluno conectado a competiçao {contestId}!')
            contest = runningContests[contestId]['contest']
            db.acquire()
            runningContests[contestId]['connected-students'] += 1
            db.release()

            # Espera disponibilizar as questões
            runningContests[contestId]['hasStarted'].acquire()

            howManyQuestions = len(contest)
            connectionSocket.send(str(howManyQuestions).encode())
            for question in contest:
                s = f"{question['q']}\n"
                for choice in question['c']:
                    s += f"  {choice}\n"

                connectionSocket.send(s.encode()) # Envia questão
                answer = int(connectionSocket.recv(2).decode()) # Recebe resposta
                db.acquire()
                question['a'][answer - 1] += 1 # Computa resposta
                db.release()

            db.acquire()
            runningContests[contestId]['connected-students'] -= 1
            db.release()
            # Verifica se era o utlimo estudante a estar respondendo
            if(runningContests[contestId]['connected-students'] == 0):
                runningContests[contestId]['sendStatistics'].release() # Se sim, libera as estatisticas
                print(f'Competição {contestId} finalizada!')

        # Finaliza a conexão
        connectionSocket.close()


    print("Servidor pronto para receber requisições!")
    while(True):
        connectionSocket, addr = serverSocket.accept()
        newThread = threading.Thread(target=connection_thread, args=(connectionSocket, addr,))
        newThread.start()

if __name__ == "__main__":
    main()
