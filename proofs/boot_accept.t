t 1
task boot_accept(panic: bool, prompt: bool, seen: bool, alive: bool, watched: int, required: int, budget: int) returns (r: bool)
  ensures r == (not panic and prompt and seen and alive and 0 <= watched and watched <= 9223372036854775807 and 0 <= required and required <= 9223372036854775807 and 0 <= budget and budget <= 9223372036854775807 and watched >= required)
{
  if watched < 0 or watched > 9223372036854775807 or required < 0 or required > 9223372036854775807 or budget < 0 or budget > 9223372036854775807 {
    r := false;
  } else {
    if panic {
      r := false;
    } else {
      if not prompt {
        r := false;
      } else {
        if not seen {
          r := false;
        } else {
          if not alive {
            r := false;
          } else {
            if watched < required { r := false; } else { r := true; }
          }
        }
      }
    }
  }
}
