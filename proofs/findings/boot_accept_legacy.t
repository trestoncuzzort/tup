t 1
task boot_accept_legacy(panic: bool, prompt: bool, seen: bool, alive: bool, watched: int, required: int, budget: int) returns (r: bool)
  ensures r == (not panic and prompt and seen and alive and 0 <= watched and watched <= 9223372036854775807 and 0 <= required and required <= 9223372036854775807 and 0 <= budget and budget <= 9223372036854775807 and watched >= required)
{
  if panic or not prompt or not seen or not alive {
    r := false;
  } else {
    if watched >= -9223372036854775808 and watched <= 9223372036854775807 and required >= -9223372036854775808 and required <= 9223372036854775807 and watched < required {
      r := false;
    } else {
      r := true;
    }
  }
}
