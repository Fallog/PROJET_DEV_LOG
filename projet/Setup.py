# -*- coding: utf-8 -*-
import utils

# Generate environement of the program

test = input("Créer environnement ? (Y/N)")

if test == "Y" :
    utils.create_folders()
    
test2 = input("Détruire environnemnt ? (Y/N)")

if test2 == "Y" :
    utils.remove_env_prog()

