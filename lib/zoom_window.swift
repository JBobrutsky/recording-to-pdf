import CoreGraphics
let l = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as! [[String:Any]]
var best = (0, 0.0)
for w in l where (w["kCGWindowOwnerName"] as? String ?? "") == "zoom.us" || (w["kCGWindowOwnerName"] as? String ?? "") == "Zoom" {
  let b = w["kCGWindowBounds"] as! [String:Any]; let a = (b["Width"] as! Double) * (b["Height"] as! Double)
  let name = w["kCGWindowName"] as? String ?? ""
  if (w["kCGWindowLayer"] as? Int ?? 1) == 0 && a > best.1 && (name.contains("Meeting") || name == "") { best = (w["kCGWindowNumber"] as! Int, a) }
  print(w["kCGWindowNumber"]!, name, b["Width"]!, b["Height"]!, w["kCGWindowLayer"]!)
}
print("BEST", best.0)
