import app.geo as geo

jsData = [
  {
    "label": "Waikaloa",
    "inputs": [(19.915403, -155.887403), 50],
    "outputs": [
        ("8e91k9qh", "8e91k9q~"), 
        ("8e91k9mh", "8e91k9m~"),
        ("8e91k9w0", "8e91k9wh"),
        ("8e91k9t0", "8e91k9th"),
      ]
  },

  {
    "label": "Brighton",
    "inputs": [(50.822327, -0.13659), 5],
    "outputs": [
      ("gcpchgut8","gcpchguth"),
      ("gcpchgums","gcpchgum~"),
      ("gcpchgut0","gcpchgut8"),
      ("gcpchgumh","gcpchgums"),
    ]
  },
]

def test_geofire():
    for testCase in jsData:
        center, radius = testCase["inputs"]
        expected = testCase["outputs"]
        observed = geo.geohashQueries(center, radius)

        assert observed == expected, testCase["label"]