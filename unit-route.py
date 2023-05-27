import pytest

from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200

def test_bibliotheque_date_ajout(client):
    response = client.get('/bibliotheque/all/date-ajout/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_date_sortie(client):
    response = client.get('/bibliotheque/all/date-sortie/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_top_consultation(client):
    response = client.get('/bibliotheque/all/top-consultation/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_top_note(client):
    response = client.get('/bibliotheque/all/top-note/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_top_favoris(client):
    response = client.get('/bibliotheque/all/top-favoris/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_sur_mediatise(client):
    response = client.get('/bibliotheque/all/sur-mediatise/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_sous_mediatise(client):
    response = client.get('/bibliotheque/all/sous-mediatise/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_sur_note(client):
    response = client.get('/bibliotheque/all/sur-note/0?client=app')
    assert response.status_code == 200

def test_bibliotheque_sous_note(client):
    response = client.get('/bibliotheque/all/sous-note/0?client=app')
    assert response.status_code == 200

def test_collection_date_ajout(client):
    response = client.get('/collection/all/date-ajout/0?client=app')
    assert response.status_code == 200

def test_collection_top_consultation(client):
    response = client.get('/collection/all/top-consultation/0?client=app')
    assert response.status_code == 200

def test_collection_top_note(client):
    response = client.get('/collection/all/top-note/0?client=app')
    assert response.status_code == 200

def test_collection_top_favoris(client):
    response = client.get('/collection/all/top-favoris/0?client=app')
    assert response.status_code == 200

def test_collection_sur_mediatise(client):
    response = client.get('/collection/all/sur-mediatise/0?client=app')
    assert response.status_code == 200

def test_collection_sous_mediatise(client):
    response = client.get('/collection/all/sous-mediatise/0?client=app')
    assert response.status_code == 200

def test_collection_sur_note(client):
    response = client.get('/collection/all/sur-note/0?client=app')
    assert response.status_code == 200

def test_collection_sous_note(client):
    response = client.get('/collection/all/sous-note/0?client=app')
    assert response.status_code == 200

def test_ma_bibliotheque_date_ajout(client):
    response = client.get('/ma-bibliotheque/Breaker/all/date-ajout/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_top_note(client):
    response = client.get('/ma-bibliotheque/Breaker/all/top-note/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_favori(client):
    response = client.get('/ma-bibliotheque/Breaker/all/favori/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_sur_mediatise(client):
    response = client.get('/ma-bibliotheque/Breaker/all/sur-mediatise/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_sous_mediatise(client):
    response = client.get('/ma-bibliotheque/Breaker/all/sous-mediatise/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_sur_note(client):
    response = client.get('/ma-bibliotheque/Breaker/all/sur-note/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_sous_note(client):
    response = client.get('/ma-bibliotheque/Breaker/all/sous-note/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_physiquement(client):
    response = client.get('/ma-bibliotheque/Breaker/all/physiquement/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_virtuellement(client):
    response = client.get('/ma-bibliotheque/Breaker/all/virtuellement/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_souhaite(client):
    response = client.get('/ma-bibliotheque/Breaker/all/souhaite/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_limite(client):
    response = client.get('/ma-bibliotheque/Breaker/all/limite/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_bibliotheque_collector(client):
    response = client.get('/ma-bibliotheque/Breaker/all/collector/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_collection_date_ajout(client):
    response = client.get('/ma-collection/Breaker/all/date-ajout/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_collection_top_note(client):
    response = client.get('/ma-collection/Breaker/all/top-note/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_collection_favori(client):
    response = client.get('/ma-collection/Breaker/all/favori/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_collection_sur_mediatise(client):
    response = client.get('/ma-collection/Breaker/all/sur-mediatise/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_collection_sous_mediatise(client):
    response = client.get('/ma-collection/Breaker/all/sous-mediatise/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_collection_sur_note(client):
    response = client.get('/ma-collection/Breaker/all/sur-note/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_ma_collection_sous_note(client):
    response = client.get('/ma-collection/Breaker/all/sous-note/0?client=app')
    assert response.status_code == 200 or (response.status_code == 400 and response.data == b'{\n  "message": "le profil de cet utilisateur n\'est pas public, si ce compte vous appartient, connectez vous pour afficher vos informations"\n}\n')

def test_get_by_ean(client):
    response = client.get('/get-by-ean/9780201379624/?client=app')
    assert response.status_code == 200