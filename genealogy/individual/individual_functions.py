from flask import session
from genealogy import db
from genealogy.models import Individual, Parents, FamilyLink
from dateutil import relativedelta
from datetime import datetime


def fullname(first, last):
    return first + " " + last


def create_partners(partner_type, father_id=None, mother_id=None):
    if db.session.query(Parents).filter_by(father_id=father_id,
                                           mother_id=mother_id).scalar() is None:
        parents = Parents(father_id, mother_id)
        db.session.add(parents)
        db.session.commit()
        db.session.flush()

        if partner_type == "parents":
            session["partners.id"] = parents.id
        elif partner_type == "patgrandparents":
            session["patgrandparents.id"] = parents.id
        elif partner_type == "matgrandparents":
            session["matgrandparents.id"] = parents.id
        elif partner_type == "child":
            pass

        return parents.id


def update_partners(partner_type, partners_id, father_id=None, mother_id=None):
    # If there is no father in the partner record, add the father to it:
    if db.session.query(Parents).filter_by(id=partners_id, father_id=father_id).scalar() is None:
        updated_father = db.session.query(Parents).get(partners_id)

        updated_father.father_id = father_id
        db.session.commit()
        db.session.flush()

        if partner_type == "parents":
            session["partners.id"] = updated_father.id
        elif partner_type == "patgrandparents":
            session["patgrandparents.id"] = updated_father.id
        elif partner_type == "matgrandparents":
            session["matgrandparents.id"] = updated_father.id

        return updated_father.id

    # Else if there is no mother in the partner record, add the mother to it:
    elif db.session.query(Parents).filter_by(id=partners_id, mother_id=mother_id).scalar() is None:
        updated_mother = db.session.query(Parents).get(partners_id)
        # parentsid = session["partners.id"]
        updated_mother.mother_id = mother_id
        db.session.commit()
        db.session.flush()

        if partner_type == "parents":
            session["partners.id"] = updated_mother.id
        elif partner_type == "patgrandparents":
            session["patgrandparents.id"] = updated_mother.id
        elif partner_type == "matgrandparents":
            session["matgrandparents.id"] = updated_mother.id

        return updated_mother.id


def link_child(individual_id, parents_id):
    if db.session.query(FamilyLink).filter_by(individual_id=individual_id,
                                              parents_id=parents_id).scalar() is None:
        c = FamilyLink(individual_id, parents_id)
        db.session.add(c)
        db.session.commit()
        db.session.flush()


def session_pop_grandparents():
    session.pop("patgrandfather.id", None)
    session.pop("patgrandmother.id", None)
    session.pop("matgrandfather.id", None)
    session.pop("matgrandmother.id", None)


def query_children(parentsid):
    children = db.session.query(Individual) \
        .join(FamilyLink) \
        .filter(FamilyLink.parents_id == parentsid) \
        .filter(FamilyLink.individual_id == Individual.id).order_by(Individual.dob)
    return children


def create_child_partnership(new_child):
    if new_child.gender == "Male":
        create_partners(partner_type="child", father_id=new_child.id, mother_id=None)
    elif new_child.gender == "Female":
        create_partners(partner_type="child", father_id=None, mother_id=new_child.id)


def add_father(form):
    father_forenames = form.father_forenames.data
    father_surname = form.father_surname.data
    father_gender = "Male"
    father_dob = form.father_dob.data
    father_dod = form.father_dod.data
    father_fullname = fullname(father_forenames, father_surname)
    father_age = calculate_period(father_dob, father_dod)

    new_father = Individual(father_surname, father_fullname, father_forenames, father_gender, father_dob, father_dod,
                            father_age)
    db.session.add(new_father)

    db.session.commit()
    db.session.flush()

    session["father.id"] = new_father.id
    session["father_fullname"] = father_fullname

    if session.get("mother.id") is None:
        create_partners(partner_type="parents", father_id=session["father.id"], mother_id=None)
    else:
        update_partners(partner_type="parents", partners_id=session["partners.id"], father_id=session["father.id"],
                        mother_id=session["mother.id"])

    return


def add_mother(form):
    mother_forenames = form.mother_forenames.data
    mother_surname = form.mother_surname.data
    mother_gender = "Female"
    mother_dob = form.mother_dob.data
    mother_dod = form.mother_dod.data
    mother_fullname = fullname(mother_forenames, mother_surname)
    mother_age = calculate_period(mother_dob, mother_dod)

    new_mother = Individual(mother_surname, mother_fullname, mother_forenames, mother_gender, mother_dob, mother_dod, mother_age)
    db.session.add(new_mother)

    db.session.commit()
    db.session.flush()
    session["mother.id"] = new_mother.id

    if session.get("father.id") is None:
        create_partners(partner_type="parents", father_id=None, mother_id=session["mother.id"])
    else:
        update_partners(partner_type="parents", partners_id=session["partners.id"], father_id=session["father.id"],
                        mother_id=session["mother.id"])

    return


def add_patGrandfather(form):
    pat_grandfather_forenames = form.patgrandfather_forenames.data
    pat_grandfather_surname = form.patgrandfather_surname.data
    pat_grandfather_gender = "Male"
    pat_grandfather_dob = form.patgrandfather_dob.data
    pat_grandfather_dod = form.patgrandfather_dod.data
    patgrandfather_fullname = fullname(pat_grandfather_forenames, pat_grandfather_surname)
    pat_grandfather_age = calculate_period(pat_grandfather_dob, pat_grandfather_dod)

    new_patgrandfather = Individual(pat_grandfather_surname, patgrandfather_fullname, pat_grandfather_forenames,
                                    pat_grandfather_gender, pat_grandfather_dob, pat_grandfather_dod, pat_grandfather_age)
    db.session.add(new_patgrandfather)

    db.session.commit()
    db.session.flush()

    session["patgrandfather.id"] = new_patgrandfather.id

    if session.get("patgrandmother.id") is None:
        create_partners(partner_type="patgrandparents", father_id=session["patgrandfather.id"], mother_id=None)
    else:
        update_partners(partner_type="patgrandparents", partners_id=session["patgrandparents.id"],
                        father_id=session["patgrandfather.id"],
                        mother_id=session["patgrandmother.id"])

    link_child(individual_id=session["father.id"], parents_id=session["patgrandparents.id"])

    return


def add_patGrandmother(form):
    patgrandmother_forenames = form.patgrandmother_forenames.data
    patgrandmother_surname = form.patgrandmother_surname.data
    patgrandmother_gender = "Female"
    patgrandmother_dob = form.patgrandmother_dob.data
    patgrandmother_dod = form.patgrandmother_dod.data
    patgrandmother_fullname = fullname(patgrandmother_forenames, patgrandmother_surname)
    pat_grandmother_age = calculate_period(patgrandmother_dob, patgrandmother_dod)

    new_patgrandmother = Individual(patgrandmother_surname, patgrandmother_fullname, patgrandmother_forenames,
                                    patgrandmother_gender, patgrandmother_dob, patgrandmother_dod, pat_grandmother_age)
    db.session.add(new_patgrandmother)

    db.session.commit()
    db.session.flush()

    session["patgrandmother.id"] = new_patgrandmother.id
    session["patGrandmother_fullname"] = patgrandmother_fullname

    if session.get("patgrandfather.id") is None:
        create_partners(partner_type="patgrandparents", father_id=None, mother_id=session["patgrandmother.id"])
    else:
        update_partners(partner_type="patgrandparents", partners_id=session["patgrandparents.id"],
                        father_id=session["patgrandfather.id"],
                        mother_id=session["patgrandmother.id"])

    link_child(individual_id=session["father.id"], parents_id=session["patgrandparents.id"])

    return


def add_matGrandfather(form):
    mat_grandfather_forenames = form.matgrandfather_forenames.data
    mat_grandfather_surname = form.matgrandfather_surname.data
    mat_grandfather_gender = "Male"
    mat_grandfather_dob = form.matgrandfather_dob.data
    mat_grandfather_dod = form.matgrandfather_dod.data
    matgrandfather_fullname = fullname(mat_grandfather_forenames, mat_grandfather_surname)
    mat_grandfather_age = calculate_period(mat_grandfather_dob, mat_grandfather_dod)

    new_matgrandfather = Individual(mat_grandfather_surname, matgrandfather_fullname, mat_grandfather_forenames,
                                    mat_grandfather_gender, mat_grandfather_dob, mat_grandfather_dod, mat_grandfather_age)
    db.session.add(new_matgrandfather)

    db.session.commit()
    db.session.flush()

    session["matgrandfather.id"] = new_matgrandfather.id

    if session.get("matgrandmother.id") is None:
        create_partners(partner_type="matgrandparents", father_id=session["matgrandfather.id"], mother_id=None)
    else:
        update_partners(partner_type="matgrandparents", partners_id=session["matgrandparents.id"],
                        father_id=session["matgrandfather.id"],
                        mother_id=session["matgrandmother.id"])

    link_child(individual_id=session["mother.id"], parents_id=session["matgrandparents.id"])

    return


def add_matGrandmother(form):
    matgrandmother_forenames = form.matgrandmother_forenames.data
    matgrandmother_surname = form.matgrandmother_surname.data
    matgrandmother_gender = "Female"
    matgrandmother_dob = form.matgrandmother_dob.data
    matgrandmother_dod = form.matgrandmother_dod.data
    matgrandmother_fullname = fullname(matgrandmother_forenames, matgrandmother_surname)
    matgrandmother_age = calculate_period(matgrandmother_dob, matgrandmother_dod)

    new_matgrandmother = Individual(matgrandmother_surname, matgrandmother_fullname, matgrandmother_forenames,
                                    matgrandmother_gender, matgrandmother_dob, matgrandmother_dod, matgrandmother_age)
    db.session.add(new_matgrandmother)

    db.session.commit()
    db.session.flush()

    session["matgrandmother.id"] = new_matgrandmother.id
    session["matgrandmother_fullname"] = matgrandmother_fullname

    if session.get("matgrandfather.id") is None:
        create_partners(partner_type="matgrandparents", father_id=None, mother_id=session["matgrandmother.id"])
    else:
        update_partners(partner_type="matgrandparents", partners_id=session["matgrandparents.id"],
                        father_id=session["matgrandfather.id"],
                        mother_id=session["matgrandmother.id"])

    link_child(individual_id=session["mother.id"], parents_id=session["matgrandparents.id"])

    return


def calculate_period(born, died):

    # If there are known birth and death dates, calculate the age
    if born and died:

        age = relativedelta.relativedelta(died, born)
        return int(age.years)

    # If the person was born over 100 years ago, don't calculate the age
    elif relativedelta.relativedelta(datetime.today(), born).years > 100:
        return None

    # If the person has no birth or death dates, don't calculate the age
    elif born is None and died is None:
        return None

    # If there is just no birth date, don't calculate the age
    elif born is None:
        return None

    # If the person was born less than 100 years ago and there's no death date, calculate current age
    elif relativedelta.relativedelta(datetime.today(), born).years < 100 and died is None:

        age = relativedelta.relativedelta(datetime.today(), born)
        return int(age.years)