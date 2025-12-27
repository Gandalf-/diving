BEGIN {
  FS = ":"
  print "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
  print "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\""
  print "        xmlns:image=\"http://www.google.com/schemas/sitemap-image/1.1\">"
}

$1 != fname {
  if (fname != "") {
    print "</url>"
  }
  fname = $1

  gsub(/.html/, "", $1)
  print "<url>"
  print "<loc>https://diving.anardil.net/" $1 "</loc>"
}

{
  print "<image:image>"
  print "<image:loc>https://diving.anardil.net" $2 "</image:loc>"
  print "</image:image>"
}

END {
  print "</url>"
  print "</urlset>"
}
