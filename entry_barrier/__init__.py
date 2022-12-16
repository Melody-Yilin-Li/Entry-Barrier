from otree.api import *
from otree.models import subsession
import csv
from numpy import random

doc = """
This is an n-player trust game with reputation system. 
Players are equally divided into two roles: buyers (A) and sellers (B). 
(X,Y) represents seller's product quality decisions.
seq_entry shows the treatment of sequential entry vs simultaneous entry.
fix_price shows the treatment of fixed price vs self-determined price.
"""


class Constants(BaseConstants):

    name_in_url = 'entry_barrier_game'
    num_rounds = 15
    players_per_group = 4
    mid_round = 6
    c_l = 5
    c_h = 30
    u_l = 60
    u_h = 95
    p_default = 55
    e_b = 20
    e_s = 10
    seq_entry = 0
    fix_price = 0


class Subsession(BaseSubsession):

    num_rounds = models.IntegerField(initial=random.randint(12, 16))

    def creating_session(self):
        if self.round_number == 1:
            players = self.get_players()

            buyer = [p for p in players if p.id_in_group % 2 == 1]
            incumbent = [p for p in players if p.id_in_group % 2 == 0 and p.id_in_group % 4 != 0]
            entrant = [p for p in players if p.id_in_group % 2 == 0 and p.id_in_group % 4 == 0]

            group_matrix = []
            while buyer:
                new_group = [
                    buyer.pop(),
                    buyer.pop(),
                    incumbent.pop(),
                    entrant.pop(),
                ]
                group_matrix.append(new_group)
            self.set_group_matrix(group_matrix)
        else:
            self.group_like_round(1)


class Group(BaseGroup):

    def set_payoffs(self):
        player_list = self.get_players()
        for p in player_list:
            if p.role() == 'buyer':
                if p.decision_buy == 0:
                    p.payoff = Constants.e_b
                else:
                    seller = self.get_player_by_id(p.decision_buy)
                    p.payoff = seller.decision_quality * Constants.u_h + (1 - seller.decision_quality) * Constants.u_l - seller.decision_price
            else:
                if p.decision_entry == 0:
                    p.payoff = Constants.e_s
                elif p.num_of_trade() > 0:
                    p.payoff = (p.decision_price - p.decision_quality * Constants.c_h - (1 - p.decision_quality) * Constants.c_l) * p.num_of_trade()
                else:
                    p.payoff = 0

    def seller_in_market(self):
        players = self.get_players()
        seller_in_market = [p for p in players if p.decision_entry == 1]
        return len(seller_in_market)


class Player(BasePlayer):

    def role(self):
        if self.id_in_group % 2 == 1:
            return 'buyer'
        else:
            return 'seller'

    def role2(self):
        if self.id_in_group % 2 == 1:
            return 'buyer'
        elif self.id_in_group % 2 == 0 and self.id_in_group % 4 != 0:
            return 'incumbent'
        else:
            return 'entrant'

    def num_of_trade(self):
        num_of_trade = 0
        player_id = self.id_in_group
        for p in self.get_others_in_group():
            if p.role() == 'buyer' and p.decision_buy == player_id:
                num_of_trade = num_of_trade + 1
        return num_of_trade

    def history_of_seller(self):
        history = []
        current = self.round_number
        for i in range(1, current):
            if self.in_round(i).num_of_trade() > 0 and self.in_round(i).decision_quality == 1:
                history.append({
                'round_number': i,
                'choice': 'Y',
                'price': self.in_round(i).decision_price,
                })
            elif self.in_round(i).num_of_trade() > 0 and self.in_round(i).decision_quality == 0:
                history.append({
                'round_number': i,
                'choice': 'X',
                'price': self.in_round(i).decision_price,
                })
            else:
                history.append({
                'round_number': i,
                'choice': 'N',
                'price': 'N',
                })
        return history

    decision_entry = models.IntegerField(
        initial=0,
        choices=[
            [0, 'No'],
            [1, 'Yes'],
        ],
        widget=widgets.RadioSelect,
    )

    decision_price = models.IntegerField()

    decision_buy = models.IntegerField(
        widget=widgets.RadioSelect,
        blank=True, 
    )

    decision_quality = models.IntegerField(
        choices=[
            [0, 'X'],
            [1, 'Y'],
        ],
        widget=widgets.RadioSelect
    )
def decision_price_min(player):
    price_minimum = (1 - Constants.fix_price) * (Constants.u_l - Constants.e_b) + Constants.fix_price * Constants.p_default
    return price_minimum

def decision_price_max(player):
    price_maximum = (1 - Constants.fix_price) * (Constants.u_h - Constants.e_b) + Constants.fix_price * Constants.p_default
    return price_maximum

def decision_buy_choices(player):
    choices = []
    players = player.get_others_in_group()
    seller_in_market = [p for p in players if p.decision_entry == 1]
    for p in seller_in_market:
        player_id = p.id_in_group
        choices.append(player_id)
    return choices

# PAGES
class Welcome(Page):
    def is_displayed(self):
        return self.round_number == 1

class Instruction1(Page):
    def is_displayed(self):
        return self.round_number == 1

class Instruction2(Page):
    def is_displayed(self):
        return self.round_number == 1

class Instruction3(Page):
    def is_displayed(self):
        return self.round_number == 1

class ShuffleWaitPage(WaitPage):
    wait_for_all_groups = True
    def is_displayed(self):
        return self.round_number <= self.subsession.num_rounds


class SellerEntry(Page):
    form_model = 'player'
    form_fields = ['decision_entry']
    #timeout_seconds = 10

    if Constants.seq_entry == 0:
        def is_displayed(self):
            return self.role() == 'seller' and self.round_number <= self.subsession.num_rounds
    else:
        def is_displayed(self):
            return self.round_number <= self.subsession.num_rounds \
                   and (self.role2() == 'incumbent' or (self.role2() == 'entrant' and self.round_number >= Constants.mid_round) )

class SellerPrice(Page):
    form_model = 'player'
    form_fields = ['decision_price']
    #timeout_seconds = 20

    if Constants.seq_entry == 0:
        def is_displayed(self):
            return self.role() == 'seller' and self.round_number <= self.subsession.num_rounds and self.decision_entry == 1
    else:
        def is_displayed(self):
            return self.round_number <= self.subsession.num_rounds and self.decision_entry == 1 \
                   and (self.role2() == 'incumbent' or (self.role2() == 'entrant' and self.round_number >= Constants.mid_round) )

    def vars_for_template(self):
        return {
            'max_price': Constants.u_h - Constants.e_b,
            'min_price': Constants.u_l - Constants.e_b
        }

class BuyerBuy(Page):
    form_model = 'player'
    form_fields = ['decision_buy']
    #timeout_seconds = 20

    def is_displayed(self):
        return self.role() == 'buyer' and self.round_number <= self.subsession.num_rounds

    def decision_buy_choices(self):
        choices = []
        players = self.get_others_in_group()
        seller_in_market = [p for p in players if p.decision_entry == 1]
        for p in seller_in_market:
            player_id = p.id_in_group
            choices.append(player_id)
        return choices

class SellerQuality(Page):
    form_model = 'player'
    form_fields = ['decision_quality']
    #timeout_seconds = 10

    if Constants.seq_entry == 0:
        def is_displayed(self):
            return self.role() == 'seller' and self.round_number <= self.subsession.num_rounds and self.decision_entry == 1 and self.num_of_trade() > 0
    else:
        def is_displayed(self):
            return self.round_number <= self.subsession.num_rounds and self.decision_entry == 1 and self.num_of_trade() > 0 \
                   and (self.role2() == 'incumbent' or (self.role2() == 'entrant' and self.round_number >= Constants.mid_round) )

class Results(Page):
    #timeout_seconds = 10

    def is_displayed(self):
        return self.round_number <= self.subsession.num_rounds

    def vars_for_template(self):
        return {
            'cumulative_payoff': sum([p.payoff for p in self.in_all_rounds()])
        }

class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()

    def is_displayed(self):
        return self.round_number <= self.subsession.num_rounds

class PlayerWaitPage(WaitPage):

    def is_displayed(self):
        return self.round_number <= self.subsession.num_rounds

page_sequence = [
    Welcome,
    Instruction1,
    Instruction2,
    Instruction3,
    ShuffleWaitPage,
    SellerEntry,
    PlayerWaitPage,
    SellerPrice,
    PlayerWaitPage,
    BuyerBuy,
    PlayerWaitPage,
    SellerQuality,
    PlayerWaitPage,
    ResultsWaitPage,
    Results
]
