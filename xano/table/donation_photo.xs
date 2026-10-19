// Stores ordered public photos associated with a donation.
table donation_photo {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int donation_id
    int position
    image photo
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "donation_id", op: "asc"}]}
  ]
  guid = "X2vTfVgqUVsVs46yqiZqTghRTn4"
}
