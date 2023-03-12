from govscentdotorg.models import Bill


class GovscentBOW:
    def create_bill_vectors(self, bill: Bill):
        pass

    def create_bill_tdif(self, bill: Bill):
        pass

    @staticmethod
    def persist_for_bill(bill: Bill):
        bill.save()

