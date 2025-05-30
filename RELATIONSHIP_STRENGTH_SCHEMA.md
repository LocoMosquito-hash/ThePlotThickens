# Relationship Strength Schema Standardization

## Summary

Successfully standardized relationship strength across all schema files to use a consistent **1-5 integer scale**.

## Changes Made

### Schema Files Updated

1. **`app/models/relationship.py`**

   - Changed: `strength = Column(Float, default=1.0)  # 0.0 to 1.0, used for visualization`
   - To: `strength = Column(Integer, default=3)  # 1-5 scale, used for visualization and relationship importance`

2. **`app/db_schema.py`**

   - Changed: `strength = Column(Float, default=1.0)  # 0.0 to 1.0, used for visualization`
   - To: `strength = Column(Integer, default=3)  # 1-5 scale, used for visualization and relationship importance`

3. **`app/db_schema_simple.py`**

   - Changed: `strength = Column(Float, default=1.0)  # 0.0 to 1.0, used for visualization`
   - To: `strength = Column(Integer, default=3)  # 1-5 scale, used for visualization and relationship importance`

4. **`app/db_schema_minimal.py`**
   - Added: `strength = Column(Integer, default=3)  # 1-5 scale, used for visualization and relationship importance`
   - (This file previously didn't have a strength column)

### Database Implementation

- **`app/relationships.py`** already had the correct implementation:
  - `ALTER TABLE relationships ADD COLUMN strength INTEGER DEFAULT 3`
  - Function parameters documented as "strength: Relationship strength (1-5)"

## Relationship Strength Scale

### Scale Definition

- **Type**: Integer
- **Range**: 1 to 5
- **Default**: 3 (medium strength)

### Meaning

- **1**: Weakest relationship
- **2**: Weak relationship
- **3**: Medium relationship (default)
- **4**: Strong relationship
- **5**: Strongest relationship

### Usage in Application

1. **Sorting/Prioritization**: Relationships sorted by strength (descending) then by update time
2. **Display**: Higher strength relationships appear first in lists
3. **Visualization**: Used for visual prominence in relationship diagrams
4. **Pair Handling**: For relationship pairs, displays the maximum strength of the two linked relationships

## Database Compatibility

- Existing database tables already use `INTEGER DEFAULT 3`
- No database migration required
- All relationship creation/update functions use the correct 1-5 scale

## Testing

- All schema files import successfully
- Relationship functions work with integer values
- Application maintains backward compatibility

## Consistency Achieved

✅ All schema definitions now use the same type, range, and default value  
✅ Documentation comments are consistent across all files  
✅ Implementation matches the documented API  
✅ No discrepancies between Float/Integer or 0.0-1.0/1-5 scales
