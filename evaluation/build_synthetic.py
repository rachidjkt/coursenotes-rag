"""Original, fictional retail operations corpus. No real merchant/customer data.

Labels are authored from these page definitions, not model-generated ground truth
or human judgments about model outputs. No language model is used by this builder.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import textwrap

VERSION = 'meridian-synthetic-v1'
BASE = Path(__file__).resolve().parent / 'synthetic_v1'
PAGES = [
    ('Atlas returns', 'en',
     'Atlas accepts unused standard goods within 21 calendar days of delivery. A return needs an authorization code from the Atlas returns desk. '
     'Approved refunds are issued to the original payment method within five business days after warehouse inspection. Shipping charges are excluded. '
     'A warranty repair is a separate process and does not extend this return window. The Boreal desk has a different policy, even when the item has the same catalogue description. '
     'A customer who sends an item without authorization receives a request for the missing code; the parcel is not automatically approved. '
     'The delivery date, not the order date, starts the window. Returned goods are inspected before being added to sellable inventory. '
     'An acceptance decision concerns the physical condition and deadline, whereas the refund timetable begins only after inspection. '
     'This page defines the standard Atlas workflow and contains no actual transactions, current stock counts, staff contacts, or legal guarantees.'),
    ('Retours Boreal', 'fr',
     'Boreal accepte les articles encore scellés dans les 14 jours calendaires suivant la livraison. Le reçu est obligatoire. '
     'Après inspection, Boreal accorde un crédit boutique sous trois jours ouvrables; aucun remboursement bancaire ne fait partie de cette procédure. '
     'La politique Atlas de remboursement ne concerne pas les commandes Boreal. Un colis déjà ouvert est dirigé vers le service de garantie et ne devient pas admissible au crédit standard. '
     'Le personnel vérifie séparément la date de livraison, le sceau et le reçu. Un reçu valide ne remplace pas un sceau intact. '
     'Le délai du crédit commence après inspection et ne correspond pas au délai de transport du colis. Une demande arrivée à temps peut encore être refusée si son état ne respecte pas cette procédure. '
     'Cette fiche décrit une politique fictive, sans données de clients, sans montant de crédit réel et sans coordonnées du personnel.'),
    ('Atlas warranty workshop', 'en',
     'The Atlas workshop covers manufacturing faults for 90 calendar days after delivery. Its remedy is repair, not a standard return refund. '
     'Cosmetic wear and accidental water damage are excluded. The customer supplies a purchase reference and a description of the fault before receiving workshop instructions. '
     'Warranty eligibility does not depend on the unopened seal used by the Boreal return policy. A repair request does not reset the original delivery date or the 21-day Atlas standard return window. '
     'The workshop records the fault category separately from the return reason so analysts do not merge the two processes. '
     'A repaired product goes through a functional check before dispatch. This document specifies no repair completion deadline and promises no replacement stock. '
     'Agents must not infer a refund promise from the word covered. These fictional rules support a training exercise about similar documents and different remedies.'),
    ('Inventory quarantine', 'en',
     'Suspected damaged inventory enters quarantine for a 12-hour inspection hold. Quarantined units are excluded from available-to-sell quantities. '
     'Only a warehouse manager can release the units after recording an inspection decision. The passage of 12 hours alone does not release stock. '
     'The stock ledger records physical presence and the quarantine flag separately; a unit can be physically present but unavailable for purchase. '
     'A shopping-cart reservation is a different state with a different expiry rule. Support agents cannot release quarantined inventory to complete a customer order. '
     'An unresolved inspection continues to block sale after the minimum hold. Counts are examples of status logic, not a live inventory feed. '
     'The inspection reason and decision are kept in the operations record, while customer-facing availability uses only eligible units. This fictional page contains no item-level stock balances.'),
    ('Réservations de panier', 'fr',
     'Une réservation de panier dure 20 minutes après sa création. Les unités réservées sont retirées du stock disponible pendant cette période. '
     'À expiration sans paiement confirmé, elles redeviennent disponibles automatiquement. Un paiement confirmé transforme la réservation en allocation de commande. '
     'Une réservation ne constitue pas une vente et ne doit pas augmenter le nombre de commandes réglées dans les indicateurs de conversion. '
     'La quarantaine pour inspection suit une règle indépendante: son expiration ne libère jamais automatiquement une unité endommagée. '
     'Le compte à rebours commence à la création de la réservation, pas au dernier clic du client. Recharger le panier ne prolonge donc pas la durée. '
     'Ces règles de simulation ne donnent ni taux réel de paiement ni nombre de paniers actifs. Elles servent à distinguer des états de stock voisins sans les confondre.'),
    ('Urban shipping', 'en',
     'Urban parcels paid before 16:00 local warehouse time enter the same-day dispatch batch. The urban delivery target is two business days after dispatch. '
     'Saturday and Sunday are not business days in this lab calendar. Orders paid at or after the cutoff enter the next business-day batch. '
     'Dispatch and delivery are separate events; the two-day target is not measured from cart creation. A remote destination follows the remote shipping sheet instead. '
     'The warehouse records payment confirmation before adding the parcel to a batch. A draft order does not qualify merely because it has an address. '
     'The target describes the fictional service design, not a carrier guarantee or a measured on-time rate. There are no real tracking numbers here. '
     'When comparing delivery options, preserve the destination category and its cutoff rather than combining the fastest terms from different service sheets.'),
    ('Expédition éloignée', 'fr',
     'Les colis vers une zone éloignée doivent être payés avant 11 h, heure locale de l’entrepôt, pour le lot du jour. La cible de livraison est de cinq jours ouvrables après expédition. '
     'Le samedi et le dimanche sont exclus du calendrier ouvrable. Un paiement à 11 h ou plus tard passe au prochain lot ouvrable. '
     'La cible urbaine de deux jours ne couvre pas ces destinations. Le délai de préparation du panier ne fait pas partie du délai de livraison après expédition. '
     'Une adresse éloignée conserve sa catégorie même si le produit est identique à un produit expédié en ville. Le suivi sépare confirmation de paiement, création du lot et remise au transporteur. '
     'Cette procédure fictive ne précise aucun tarif postal, aucune taxe ni aucune garantie de transport. Les délais cibles ne sont pas des observations de performance réelle.'),
    ('Analytics consent', 'en',
     'Optional analytics events are collected only after explicit opt-in. Raw consented events are deleted after 180 days. '
     'Exported analytical aggregates must omit email addresses. Refusing optional analytics does not block checkout. '
     'The event retention period does not define the retention period for support logs, which use another schedule. Analysts should not join exported aggregates to contact details to recreate individual browsing histories. '
     'An opt-in records a preference for this fictional exercise and is not a substitute for reviewing applicable privacy requirements in a real deployment. '
     'The page defines collection and export rules, not a sample of customer events. It contains no measured opt-in rate, order count, or experimental result. '
     'Separate consent state from conversion outcomes so an analyst cannot mistake missing optional events for a failed purchase. The checkout service keeps its own operational records.'),
    ('Support log retention', 'en',
     'Operational support logs are retained for 30 days. A log may contain a support ticket identifier but must not contain full payment-card details. '
     'Deleting a support log does not cancel an order or erase the separate purchase ledger. The 180-day optional analytics schedule does not apply to these logs. '
     'Agents record the kind of issue and resolution state rather than copying entire customer conversations into diagnostic logs. '
     'A ticket identifier links the support workflow without supplying a public contact directory. The logs are operational diagnostics and are not a source of verified purchase totals. '
     'This fictional schedule is a training constraint, not legal advice or a universal retention requirement. No real customer text, ticket history, or card number appears in the corpus. '
     'When describing retention, name the record category rather than reporting a single duration for every system.'),
    ('Checkout conversion experiment', 'en',
     'The checkout experiment runs for 14 full days without early stopping. Its conversion metric is settled orders divided by eligible sessions. '
     'Known bot sessions are excluded from the denominator. Revenue and campaign clicks are not the numerator of this conversion metric. '
     'The variant assignment is held stable during the observation window. Analysts document exclusions before reading the experiment outcomes. '
     'No observed lift, significance value, sample size, or winning variant is provided on this page. The duration is a protocol choice, not evidence that a result has been achieved. '
     'An order with an unconfirmed payment is not settled. A support ticket and an inventory reservation are also not settled orders. '
     'The fictional experiment teaches metric definition and separation between protocol and measured results; it supplies no data for computing a numerical conversion rate.'),
    ('Return-rate metric', 'en',
     'The operational return-rate report uses a rolling 30-day window. Its numerator is returned order lines and its denominator is fulfilled order lines. '
     'Cancelled lines are excluded from both quantities. The unit is an order line, not a whole order, customer, or browsing session. '
     'A replacement under warranty is tagged separately and must not silently enter the standard-return numerator. Analysts preserve the same observation window for numerator and denominator. '
     'An item awaiting inspection is not yet counted as an approved returned line. The report definition differs from the checkout experiment conversion metric and the email campaign click metric. '
     'This document defines a measurement only. It includes no actual counts and cannot support a numerical current return rate. A high rate cannot be inferred from the existence of a return policy.'),
    ('Indicateur de campagne', 'fr',
     'Le taux de clic de campagne est le nombre de destinataires uniques ayant cliqué divisé par le nombre de messages livrés. Les achats ne font pas partie du numérateur. '
     'Les messages rejetés ne sont pas des messages livrés. Plusieurs clics du même destinataire ne créent pas plusieurs personnes au numérateur. '
     'Cette définition ne correspond pas à la conversion du passage en caisse, qui repose sur des commandes réglées et des sessions admissibles. '
     'Le tableau de campagne sépare les clics des ouvertures et ne permet pas de déduire des revenus à partir des seuls clics. Aucune valeur observée ni variante gagnante n’est indiquée. '
     'La fiche appartient à un laboratoire fictif et ne contient aucune adresse de destinataire. Elle permet de tester si une réponse retrouve la bonne définition parmi plusieurs indicateurs proches.'),
    ('Incident escalation drill', 'en',
     'During a suspected data incident, the on-call lead must be notified internally within two hours of discovery. A first internal situation note is due within 24 hours. '
     'These are fictional internal drill targets, not statutory external notification deadlines. The note records what is known and explicitly labels uncertainties. '
     'An agent should not delay escalation while waiting to prove the cause. The investigation timeline keeps discovery, internal notification, and later updates separate. '
     'This page defines no public hotline, regulatory reporting rule, affected-user count, or confirmed breach. A routine return request is not automatically an incident. '
     'The training exercise focuses on distinguishing an internal response target from evidence of an actual event. It provides no real incident report or personal information.'),
    ('Nightly stock reconciliation', 'en',
     'The stock reconciliation job starts nightly at 01:30 UTC. It compares the physical-count ledger with allocations, reservations, and quarantine states. '
     'A mismatch creates an operations review item; the job never silently increases available stock to balance the books. '
     'The job schedule is independent of the warehouse local-time shipping cutoffs. UTC is used so analysts can compare logs from different warehouse clocks. '
     'A unit reserved in a cart is not missing stock, and a quarantined unit can be physically present without being sellable. Reviewers examine these states before calling a difference a loss. '
     'The procedure supplies no current balance for any SKU and no measured reconciliation error rate. It explains how to respond to differences, not how many differences occurred. This is fictional operations documentation.'),
    ('Emballages réutilisables', 'fr',
     'Les emballages réutilisables du laboratoire portent une étiquette bleue. Les emballages à usage unique portent une étiquette grise. '
     'Le personnel sépare ces deux flux lors du tri et note seulement la catégorie d’emballage dans le suivi logistique. '
     'La couleur ne représente ni la vitesse de livraison ni le statut de quarantaine du produit. Un colis éloigné peut utiliser le même emballage réutilisable qu’un colis urbain. '
     'Cette fiche ne fixe aucune consigne monétaire et aucun rabais client. Elle ne publie pas de mesure d’impact environnemental, de poids économisé ou de taux de retour des contenants. '
     'Les exemples sont fictifs et servent à éviter qu’un système transforme une convention de tri en promesse commerciale ou en résultat environnemental. Le contenu du colis reste soumis aux contrôles habituels.'),
    ('Loyalty points', 'en',
     'The lab loyalty scheme awards two points per Canadian dollar of merchandise subtotal before tax. Shipping charges do not earn points. '
     'Unused points expire after 180 days from the award date. This expiry is unrelated to analytics event deletion, despite the matching duration. '
     'A refund reverses the points awarded for the refunded merchandise. Agents do not award points merely for opening a support ticket or clicking a campaign message. '
     'The subtotal is the merchandise amount after item discounts and before tax, not the entire charged total. The scheme definition contains no current customer point balances or redemption value. '
     'A numerical example would need an eligible merchandise amount, which this page deliberately does not provide. These rules belong only to the fictional training store.'),
    ('Routage du soutien', 'fr',
     'Les demandes rédigées en français sont dirigées vers la file B. Les demandes rédigées en anglais vont dans la file A. '
     'Une demande urgente de niveau P1 a une cible de premier accusé de réception de 30 minutes. Cet accusé n’est pas une promesse de résolution. '
     'Le choix de file dépend de la langue de la demande et non du pays de livraison. Un retour Boreal peut donc être traité dans la file A si le message est en anglais. '
     'Le routage ne fournit aucun numéro de téléphone, adresse du personnel ni calendrier de permanence. La cible P1 décrit une procédure fictive et non une performance mesurée. '
     'Les agents distinguent réception, attribution et résolution dans le suivi du ticket. Le laboratoire ne publie ici ni conversations clients ni statistiques de temps de traitement.'),
    ('Catalogue import contract', 'en',
     'Catalogue imports require the columns sku, title, price_cad, and status. Imported items must have status draft. '
     'A duplicate sku rejects the entire import batch; it does not overwrite the existing catalogue item. Validation happens before the batch is applied. '
     'A later publishing step is separate from import validation. A valid draft price does not imply that a product is currently sold at that amount. '
     'The contract specifies column names and rejection behavior but contains no actual catalogue rows, inventory balances, prices, forecasts, or product photographs. '
     'The sku field identifies a catalogue record, whereas a support ticket identifier identifies a service interaction. The two identifiers are not interchangeable. '
     'This fictional batch contract supports testing of precise source retrieval and prevents an answer from inventing missing product details.'),
]


def question(identifier, split, language, text, pages, reference, quote='', cross_language=False):
    return {'id': identifier, 'split': split, 'language': language, 'cross_language': cross_language,
            'corpus_version': VERSION, 'question': text, 'answerable': bool(pages),
            'sources': [{'filename': 'meridian.pdf', 'page': page} for page in pages],
            'reference_answer': reference, 'support_quote': quote, 'verified': True,
            'label_provenance': 'Synthetic author-defined labels; exact supporting quote checked by builder; not independent human review.'}


QUESTIONS = [
    question('dev01','development','en','What is the Atlas standard return window, and when does its refund arrive?',[1], 'Within 21 calendar days of delivery; original-payment refund within five business days after inspection.', 'within 21 calendar days'),
    question('dev02','development','en','For Boreal, must goods remain sealed, and is the remedy bank money or store credit?',[2], 'Goods must remain sealed; Boreal grants store credit, not a bank refund.', 'un crédit boutique sous trois jours',True),
    question('dev03','development','fr','Combien de temps la garantie Atlas couvre-t-elle les défauts de fabrication ?',[3], '90 jours calendaires après livraison; la réparation est le remède.', 'for 90 calendar days',True),
    question('dev04','development','en','Does a quarantine inspection hold automatically release units after twelve hours?',[4], 'No; only a warehouse manager can release them after an inspection decision.', 'Only a warehouse manager can release'),
    question('dev05','development','en','What are the urban dispatch cutoff and delivery target?',[6], 'Before 16:00 local warehouse time; two business days after dispatch.', 'before 16:00 local warehouse time'),
    question('dev06','development','fr','Peut-on collecter les événements analytiques facultatifs sans consentement explicite ?',[8], 'Non; la collecte exige un consentement explicite et le refus ne bloque pas le paiement.', 'only after explicit opt-in',True),
    question('dev07','development','en','How is checkout conversion defined, and are known bots eligible sessions?',[10], 'Settled orders divided by eligible sessions; known bot sessions are excluded.', 'settled orders divided by eligible sessions'),
    question('dev08','development','fr','Quel est le numérateur du taux de clic de campagne ?',[12], 'Le nombre de destinataires uniques ayant cliqué; les achats en sont exclus.', 'destinataires uniques ayant cliqué'),
    question('dev09','development','en','Do shipping charges earn loyalty points, and when do unused points expire?',[16], 'Shipping does not earn points; unused points expire 180 days from award.', 'Shipping charges do not earn points'),
    question('dev10','development','en','What is the personal email address of the Atlas returns manager?',[], 'Unsupported: no staff contact directory is provided.'),
    question('dev11','development','fr','Combien d’unités du produit PINE-42 sont disponibles en ce moment ?',[], 'Non documenté: aucun solde de stock réel par produit.'),
    question('dev12','development','en','How many real shoppers completed checkout yesterday?',[], 'Unsupported: the corpus supplies definitions, not observed shopping counts.'),
    question('held01','held_out','en','How long does a cart reservation last, and does refreshing extend it?',[5], '20 minutes after creation; refreshing does not extend it.', 'Une réservation de panier dure 20 minutes',True),
    question('held02','held_out','fr','Quels sont le seuil horaire et la cible de livraison pour une zone éloignée ?',[7], 'Paiement avant 11 h locale; cinq jours ouvrables après expédition.', 'avant 11 h'),
    question('held03','held_out','fr','Pendant combien de temps les journaux opérationnels du soutien sont-ils conservés ?',[9], '30 jours; leur suppression ne supprime pas le registre des achats.', 'retained for 30 days',True),
    question('held04','held_out','en','What unit and denominator does the return-rate report use?',[11], 'Returned order lines divided by fulfilled order lines, with cancelled lines excluded.', 'denominator is fulfilled order lines'),
    question('held05','held_out','fr','Quel délai vise la notification interne d’un incident et est-ce une échéance légale externe ?',[13], 'Deux heures après découverte; c’est une cible interne fictive, pas une échéance légale externe.', 'within two hours of discovery',True),
    question('held06','held_out','en','When does stock reconciliation run, and does a mismatch automatically increase sellable stock?',[14], 'Nightly at 01:30 UTC; a mismatch creates a review item and never silently increases stock.', 'nightly at 01:30 UTC'),
    question('held07','held_out','en','Which label color identifies reusable packaging, and does this define a cash deposit?',[15], 'Blue; no monetary deposit is specified.', 'une étiquette bleue',True),
    question('held08','held_out','en','Which queue handles French support requests, and what does the P1 thirty-minute target promise?',[17], 'Queue B; first acknowledgment, not resolution.', 'vers la file B',True),
    question('held09','held_out','fr','Quelles colonnes exige un import catalogue, et que provoque un sku dupliqué ?',[18], 'sku, title, price_cad et status; un doublon rejette tout le lot.', 'rejects the entire import batch',True),
    question('held10','held_out','en','Compare the Atlas and Boreal standard return windows and refund remedies.',[1,2], 'Atlas: 21 days and original-payment refund; Boreal: 14 days and store credit.'),
    question('held11','held_out','fr','Comparez les cibles de livraison urbaine et éloignée après expédition.',[6,7], 'Deux jours ouvrables en ville, cinq jours ouvrables en zone éloignée.'),
    question('held12','held_out','en','Do raw optional analytics events and operational support logs share one retention duration?',[8,9], 'No; analytics events: 180 days, support logs: 30 days.'),
    question('held13','held_out','en','What was the measured conversion lift of the winning checkout variant?',[], 'Unsupported: no observed lift or winning variant is supplied.'),
    question('held14','held_out','fr','Quel est le numéro de téléphone direct de la file B ?',[], 'Non documenté: aucune coordonnée téléphonique.'),
    question('held15','held_out','en','What is the full payment-card number of the last customer?',[], 'Unsupported: no actual customer or payment-card data is supplied.'),
    question('held16','held_out','fr','Quel est le prix de vente actuel du produit PINE-42 ?',[], 'Non documenté: aucun prix de produit réel.'),
]


def build():
    from reportlab.pdfgen import canvas
    BASE.mkdir(parents=True, exist_ok=True)
    source = {'version': VERSION, 'synthetic': True, 'provenance': 'Original fictional policies authored for this project; no real merchant or customer data.',
              'pages': [{'page': i, 'title': title, 'language': language, 'text': text} for i,(title,language,text) in enumerate(PAGES,1)]}
    (BASE/'corpus.json').write_text(json.dumps(source, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    pdf = canvas.Canvas(str(BASE/'meridian.pdf'), invariant=1, pagesize=(612,792))
    pdf.setTitle('Meridian synthetic operations lab v1')
    pdf.setAuthor('CourseNotes synthetic fixture')
    for page, (title, language, text) in enumerate(PAGES, 1):
        pdf.setFont('Helvetica-Bold', 15)
        pdf.drawString(40, 748, title)
        pdf.setFont('Helvetica', 9)
        pdf.drawString(40, 729, f'SYNTHETIC / FICTIF — {VERSION} — physical page {page}')
        block = pdf.beginText(40, 700)
        block.setFont('Helvetica', 11)
        block.setLeading(17)
        for line in textwrap.wrap(text, width=86):
            block.textLine(line)
        pdf.drawText(block)
        pdf.showPage()
    pdf.save()
    for row in QUESTIONS:
        if row['support_quote']:
            assert any(row['support_quote'] in PAGES[ref['page']-1][2] for ref in row['sources']), row['id']
    for split, name in [('development','development.jsonl'), ('held_out','held_out.jsonl')]:
        rows = [q for q in QUESTIONS if q['split'] == split]
        (BASE/name).write_text(''.join(json.dumps(q,ensure_ascii=False)+'\n' for q in rows), encoding='utf-8', newline='\n')
    protocol = {'corpus_version': VERSION, 'synthetic': True, 'preliminary': True,
                'pages': 18, 'questions': 28, 'development_questions': 12, 'held_out_questions': 16,
                'k': 3, 'chunk_size': 900, 'chunk_overlap': 150,
                'policy': 'Finalize source/configuration on development only; commit before held-out execution; run held-out once and report without tuning against it.',
                'labels': 'Author-defined synthetic references, not independent human judgments of generated answers.',
                'metrics': ['initial retrieval hit rate', 'mean page Recall@3', 'all supporting pages at 3', 'answerable abstention', 'unsupported abstention', 'citation validation failures', 'errors', 'mean/median/p95 latency'],
                'files_sha256': {name: hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in ('corpus.json','meridian.pdf','development.jsonl','held_out.jsonl')}}
    (BASE/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n',encoding='utf-8', newline='\n')
    print(json.dumps({'pages':len(PAGES),'questions':len(QUESTIONS),'output':'evaluation/synthetic_v1'}))


if __name__ == '__main__':
    build()
    if '--prepare-demo' in sys.argv:
        runtime = BASE.parents[1]/'.demo_runtime'/'documents'
        runtime.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BASE/'meridian.pdf', runtime/'meridian.pdf')
        print('Shareable PDF copied to .demo_runtime/documents; index separately using COURSENOTES_HOME.')
