from odoo_exact_controller import *

'''  kan niet py.test framework gebruiken omdat die standaard de __init__.py uitvoeert en dan worden in dit geval 
     ongewenste modules geladen
     let op er zijn ook boekingen gedaan (transactions)
     let op klanten met code > 7000xxx negeren, want dat zijn leveranciers toegevoegd door Debbie
'''

#class TestController:
#    def func(self, invoice_id):
#        return export_invoice_to_exact(invoice_id)
#    
#    def test_export_invoice(self, invoice_id):
#        exact_order_number = self.func(invoice_id)
#        assert str(exact_order_number).isdigit()
#test = TestController()
#test.test_export_invoice(45)


# if deleting relations, then contacts are deleted as well!
def delete_relation(relation_id):
    try:
        print "trying to delete relation {0}".format(relation_id)
        rel = exact.api.relations.filter(filter="ID eq guid'%s'" % (relation_id,))
        if rel:
            rel = rel[0]
            try:
                res = exact.api.relations.delete(rel['ID'])
            except HTTPError as e:
                print "fout bij verwijderen relatie: {0}".format(e.response)
        else:
            print "relation does not exists {0}".format(relation_id)
    except ObjectDoesNotExist:
        print "relation {0} does not exist".format(relation_id)



exact = Exact()
div_code = '1673399'  # (1673298=dacombv / 1673399=dfi / 1557337=demo)
exact.set_division_code(div_code)  #dacom bv

print "trying to get the total number of relations which are NOT SUPPLIERS..."
total_number_of_relations = len(exact.get_all_relations())
print "total number of relations = {0}".format(total_number_of_relations)

# invoices
relations_without_invoices = exact.get_relations_without_invoices()
total_number_of_relations_without_invoices = len(relations_without_invoices)
print "number of relations without invoices = {0}".format(total_number_of_relations_without_invoices)

relations_with_invoices = exact.get_relations_with_invoices()
total_number_of_relations_with_invoices = len(relations_with_invoices)
print "number of relations with invoices = {0}".format(total_number_of_relations_with_invoices)

relations_with_translines = exact.get_relations_with_transactionlines()
total_number_of_relations_with_translines = len(relations_with_translines)
print "number of relations with transactionlines = {0}".format(total_number_of_relations_with_translines)


# delete users WITHOUT invoices UNLESS they have transactionlines...
relations_to_be_deleted = []
for relation in relations_without_invoices:
    relation_code = relation.keys()[0]
    relations_to_be_deleted.append(relation_code)


# relations met transactionlines hieruit filteren
for relation in relations_with_translines:
    relation_code = relation.keys()[0]
    if relation_code in relations_to_be_deleted:
        relations_to_be_deleted.remove(relation_code)


# relations to keep
# keep users WITH invoices OR with transactionlines...
relations_to_keep = []
for relation in relations_with_invoices:
    relation_code = relation.keys()[0]
    relations_to_keep.append(relation_code)


# relations met transactionlines hieraan toevoegen
for relation in relations_with_translines:
    relation_code = relation.keys()[0]
    if relation_code not in relations_to_keep:
        relations_to_keep.append(relation_code)


total_number_of_relations_to_keep = len(relations_to_keep)
print "number of relation to keep: {0}".format(total_number_of_relations_to_keep)

print "relations to keep (ID, Name, Code):"
for relation in relations_to_keep:
    exact_rel = exact.api.relations.filter(filter="ID eq guid'%s'" % (relation,))[0]
    name = exact_rel.get('Name')
    code = exact_rel.get('Code').strip()
    #print "{0};{1};{2}".format(relation, name, code)
    print "{0};{1}".format(relation, code)



# relations to delete
total_number_of_relations_to_be_deleted = len(relations_to_be_deleted)
print "number of relations to be deleted: {0}".format(total_number_of_relations_to_be_deleted)

print "relations to be deleted (ID, Name, Code):"
for relation in relations_to_be_deleted:
    exact_rel = exact.api.relations.filter(filter="ID eq guid'%s'" % (relation,))[0]
    name = exact_rel.get('Name')
    code = exact_rel.get('Code').strip()
    #print "{0};{1};{2}".format(relation, name, code)
    print "{0};{1}".format(relation, code)


print "going to actually delete the relations"
for relation in relations_to_be_deleted:
    delete_relation(relation)
