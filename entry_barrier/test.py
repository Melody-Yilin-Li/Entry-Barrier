from otree.api import *
from ._builtin import Bot
import random



class PlayerBot(Bot):

    def play_round(self):
        if self.player.round_number == 1:
            yield (pages.WelcomePage)

        if self.player.id_in_group == 1:
            yield (pages.SellerReward)
            yield Submission(pages.SellerSendBack, {'quality_amount': random.randint(0, self.group.invest_amount)}, timeout_happened=True)
        else:
            yield Submission(pages.BuyerSend, {'invest_amount': C.endowment}, timeout_happened=True)
            yield Submission(pages.BuyerFeedback, {'feedback_choice': random.choice([False, True]), 'feedback_amount': random.randint(1, 7)}, timeout_happened=True)

        yield Submission(pages.ResultsSend, timeout_happened=True)

        if self.player.id_in_group == 1:
            if self.group.invest_amount == 0:
                p1_expected_payoff = C.endowment
            elif self.group.feedback_choice == False:
                p1_expected_payoff = C.endowment + self.group.invest_amount - self.group.quality_amount
            else:
                p1_expected_payoff = C.endowment + self.group.invest_amount - self.group.quality_amount - self.group.reward_amount
            assert self.player.payoff == p1_expected_payoff

            if self.group.feedback_choice == True:
                p1_expected_reputation = self.group.feedback_amount
            else:
                p1_expected_reputation = 0
            assert self.player.current_reputation == p1_expected_reputation

        else:
            if self.group.invest_amount == 0:
                p2_expected_payoff = C.endowment
            elif self.group.feedback_choice == False:
                p2_expected_payoff = C.endowment - self.group.invest_amount + self.group.quality_amount * C.multiplier
            else:
                p2_expected_payoff = C.endowment - self.group.invest_amount + self.group.quality_amount * C.multiplier - self.subsession.feedback_cost() + self.group.reward_amount
            assert self.player.payoff == p2_expected_payoff

            if self.group.feedback_choice == True:
                p2_expected_reputation = self.group.feedback_amount
            else:
                p2_expected_reputation = 0
            assert self.player.current_reputation == p2_expected_reputation






