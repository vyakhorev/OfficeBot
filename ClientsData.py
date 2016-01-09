from random import choice, randint
class Client:
    def __init__(self, name):
        self.name = name
        self.data = None

    def set_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

def make_test_client():
    clients_alliases = ['Client1', 'Client2', 'Client3', 'Client4', 'Client5', 'Client6', 'SpecialClient1',
                        'Client7', 'Client8']
    some_data = ['we', 'defeat', 'loose', 'regex', 'inline', 'telegram', 'good', 'bad', 'neutral']

    clients = {}
    for cl_i in clients_alliases:
        temp_cl = Client(cl_i)
        temp_data = ' '.join([choice(some_data) for i in range(randint(6,12))])
        temp_cl.set_data(temp_data)
        clients[cl_i] = temp_cl

    return clients

# testing
if __name__ == '__main__':
    f = make_test_client()
    for cl in f.items():
        print(cl)