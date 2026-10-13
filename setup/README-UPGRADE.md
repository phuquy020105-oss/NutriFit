# Database upgrade notes

1. Back up NutriFitDB first.
2. Run `upgrade_existing_database.sql` when upgrading an existing database. It only adds missing premium/nutrition structures.
3. Do not rerun `create_database.sql` against the existing DB: the original main script includes DROP TABLE statements. Use it only to provision a brand-new empty development database.
4. Import catalog data with `python setup\seed_nutrition_catalog.py --apply --database NutriFitDB`.
