import smartpy as sp 

class Lottery(sp.Contract):
    def __init__(self):
        # STORAGE
        self.init(
            players=sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost=sp.tez(1),
            max_tickets=sp.nat(5),
            tickets_available=sp.nat(5),
            operator = sp.test_account("admin").address
        )

    @sp.entry_point
    def buy_ticket(self, params):
        sp.set_type(params, sp.TRecord(purchase_amount = sp.TNat))
        #assertions
        sp.verify(params.purchase_amount > 0, "INVALID NUMBER OF TICKETS")
        sp.verify(self.data.tickets_available - params.purchase_amount >= 0, "NOT ENOUGH TICKETS AVAILABLE")
        sp.verify(sp.amount >= sp.mul(self.data.ticket_cost, params.purchase_amount), "INVALID AMOUNT")

        #storage changes
        sp.for i in sp.range(0, params.purchase_amount, step=1):
            self.data.players[sp.len(self.data.players)] = sp.sender
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - params.purchase_amount)

        #return extra tez
        extra_amount = sp.amount - sp.mul(self.data.ticket_cost, params.purchase_amount)
        sp.if extra_amount > sp.tez(0):
            sp.send(sp.sender, extra_amount)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        #assertions
        sp.verify(self.data.tickets_available == 0, "GAME IS STILL ON")
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORISED")

        #generate winner
        winner_index = random_number % sp.len(self.data.players)
        winner_address = self.data.players[winner_index]

        #send reward to winner
        sp.send(winner_address, sp.balance)

        #reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_cost(self, params):
        sp.set_type(params, sp.TRecord(new_cost = sp.TNat))
        #assertions
        sp.verify(params.new_cost > 0, "INVALID PRICE")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "LOTTERY CURRENTLY UNDERWAY")
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORISED")

        #storage changes
        self.data.ticket_cost = sp.mul(sp.tez(1), params.new_cost)

        #reset the game, just in case
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_max_tickets(self, params):
        sp.set_type(params, sp.TRecord(new_max_tickets = sp.TNat))
        #assertions
        sp.verify(params.new_max_tickets > 0, "INVALID VALUE")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "LOTTERY CURRENTLY UNDERWAY")
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORISED")

        #storage changes
        self.data.max_tickets = params.new_max_tickets
        self.data.tickets_available = params.new_max_tickets

        #reset the game, just in case
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets


@sp.add_test(name="main")
def test():
    scenario = sp.test_scenario()

    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    john = sp.test_account("john")
    mike = sp.test_account("mike") 
    charles = sp.test_account("charles")


    lottery = Lottery()
    scenario += lottery
    scenario += lottery.buy_ticket(purchase_amount=sp.as_nat(1)).run(
        amount=sp.tez(1), sender=alice
    )
    scenario += lottery.buy_ticket(purchase_amount=sp.as_nat(1)).run(
        amount=sp.tez(10), sender=bob
    )
    scenario += lottery.buy_ticket(purchase_amount=sp.as_nat(3)).run(
        amount=sp.tez(3), sender=john
    )
    scenario += lottery.end_game(sp.as_nat(23)).run(
        now = sp.timestamp(3), sender = admin
    )

    scenario += lottery.change_cost(new_cost=sp.as_nat(4)).run(
        now = sp.timestamp(3), sender = admin
    )
    scenario += lottery.buy_ticket(purchase_amount=sp.as_nat(1)).run(
        amount=sp.tez(4), sender=alice
    )
    scenario += lottery.buy_ticket(purchase_amount=sp.as_nat(4)).run(
        amount=sp.tez(16), sender=bob
    )
    scenario += lottery.end_game(sp.as_nat(23)).run(
        now = sp.timestamp(3), sender = admin
    )
    

    scenario += lottery.change_max_tickets(new_max_tickets=sp.as_nat(8)).run(
        now = sp.timestamp(3), sender = admin
    )
    scenario += lottery.buy_ticket(purchase_amount=sp.as_nat(6)).run(
        amount=sp.tez(24), sender=alice
    )
    scenario += lottery.buy_ticket(purchase_amount=sp.as_nat(2)).run(
        amount=sp.tez(8), sender=bob
    )
    scenario += lottery.end_game(sp.as_nat(23)).run(
        now = sp.timestamp(3), sender = admin
    )
    