from multiple_aquarium_logic import create_aquarium, add_fish, get_all_aquariums

# Create aquarium (saved to database)
create_aquarium("My Tank", 200)

# Add fish (saved to database)  
add_fish(1, "Neon Tetra", 3)

# Retrieve all data (from database)
aquariums = get_all_aquariums()