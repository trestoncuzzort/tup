method Boot_accept(panic: bool, prompt: bool, seen: bool, alive: bool, watched: int, required: int, budget: int) returns (r: bool)
  ensures (r == ((!panic) && prompt && seen && alive && (0 <= watched) && (watched <= 9223372036854775807) && (0 <= required) && (required <= 9223372036854775807) && (0 <= budget) && (budget <= 9223372036854775807) && (watched >= required)))
{
  r := false;
}

lemma t_refutation_certificate()
  ensures (!(false == ((!false) && (0 <= 0) && (0 <= 9223372036854775807) && (0 <= 0) && (0 <= 9223372036854775807) && (0 <= 0) && (0 <= 9223372036854775807) && (0 >= 0))))
{
}
