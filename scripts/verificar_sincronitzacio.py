#!/usr/bin/env python3
"""
Script per verificar si les assignatures de la base de dades
estàn sincronitzades amb les de la web UOC.
"""

from scraper import llegir_assignatures_grau, obtenir_llista_graus_uoc, esborrar_cache
from base_dades import obtenir_assignatures, obtenir_graus
import time

def main():
    esborrar_cache()
    
    print('=' * 60)
    print('ANÀLISI DE SINCRONITZACIÓ: WEB UOC vs BASE DE DADES')
    print('=' * 60)
    print()
    
    # Obtenir totes les assignatures de la BD
    all_bd = obtenir_assignatures()
    all_bd_codes = {a['codi'] for a in all_bd}
    print(f'Total assignatures a la BD: {len(all_bd)}')
    print(f'Total codis únics a la BD: {len(all_bd_codes)}')
    print()
    
    # Per cada grau, obtenir de la web i comparar
    graus = obtenir_llista_graus_uoc()
    total_web = 0
    total_bd_by_grau = 0
    
    for grau in graus:
        print(f'--- {grau["nom"]} ---')
        try:
            web_assignatures = llegir_assignatures_grau(grau['url'])
            web_codes = {a['codi'] for a in web_assignatures}
            total_web += len(web_assignatures)
            
            # Obtenir assignatures d'aquest grau de la BD
            bd_for_grau = []
            for a in all_bd:
                if a['graus'] and grau['nom'] in a['graus']:
                    bd_for_grau.append(a)
            
            bd_codes = {a['codi'] for a in bd_for_grau}
            total_bd_by_grau += len(bd_for_grau)
            
            missing_in_bd = web_codes - bd_codes
            missing_in_web = bd_codes - web_codes
            
            print(f'  Web: {len(web_assignatures):3d} assignatures')
            print(f'  BD:  {len(bd_for_grau):3d} assignatures')
            print(f'  Diferència: {len(missing_in_bd) - len(missing_in_web):4d}')
            
            if missing_in_bd:
                print(f'  ⚠️  Falten a BD: {len(missing_in_bd)} assignatures')
                if len(missing_in_bd) <= 10:
                    print(f'     Codis: {sorted(missing_in_bd)}')
                else:
                    print(f'     Exemples: {sorted(list(missing_in_bd)[:10])}...')
            
            if missing_in_web:
                print(f'  ⚠️  Falten a WEB: {len(missing_in_web)} assignatures')
                if len(missing_in_web) <= 10:
                    print(f'     Codis: {sorted(missing_in_web)}')
                else:
                    print(f'     Exemples: {sorted(list(missing_in_web)[:10])}...')
            
            if not missing_in_bd and not missing_in_web:
                print(f'  ✅ Sincronitzat!')
            
            print()
            time.sleep(1)  # Per no sobrecarregar la web
            
        except Exception as e:
            print(f'  ❌ Error: {e}\n')
    
    print('=' * 60)
    print('RESUM TOTAL')
    print('=' * 60)
    print(f'Total a la web:        {total_web:3d} assignatures')
    print(f'Total a la BD:         {total_bd_by_grau:3d} assignatures')
    print(f'Diferència:           {total_web - total_bd_by_grau:4d} assignatures')
    print()
    
    # Also check total unique codes
    all_web_codes = set()
    for grau in graus:
        try:
            web_assignatures = llegir_assignatures_grau(grau['url'])
            all_web_codes.update({a['codi'] for a in web_assignatures})
        except:
            pass
    
    print(f'Codis únics a la web: {len(all_web_codes)}')
    print(f'Codis únics a la BD:  {len(all_bd_codes)}')
    print(f'Codis que falten a BD:  {len(all_web_codes - all_bd_codes)}')
    print(f'Codis que falten a WEB: {len(all_bd_codes - all_web_codes)}')

if __name__ == "__main__":
    main()
