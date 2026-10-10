method Boot_accept(panic: bool, prompt: bool, seen: bool, alive: bool, watched: int, required: int, budget: int) returns (r: bool)
  ensures (r == ((!panic) && prompt && seen && alive && (0 <= watched) && (watched <= 9223372036854775807) && (0 <= required) && (required <= 9223372036854775807) && (0 <= budget) && (budget <= 9223372036854775807) && (watched >= required)))
{
  if ((watched < 0) || (watched > 9223372036854775807) || (required < 0) || (required > 9223372036854775807) || (budget < 0) || (budget > 9223372036854775807)) {
    r := false;
  } else {
    if panic {
      r := false;
    } else {
      if (!prompt) {
        r := false;
      } else {
        if (!seen) {
          r := false;
        } else {
          if (!alive) {
            r := false;
          } else {
            if (watched < required) {
              r := false;
            } else {
              r := true;
            }
          }
        }
      }
    }
  }
}
